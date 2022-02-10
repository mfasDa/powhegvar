
#include "Pythia8/Pythia.h"
#include "Pythia8Plugins/PowhegHooks.h"
#include "Pythia8/ParticleData.h"
// using namespace Pythia8;

#include <TROOT.h>
#include <TSystem.h>
#include <TH1F.h>
#include <TProfile.h>
#include <TClonesArray.h>
#include <TPythia8.h>
#include <TParticle.h>
#include <TDatabasePDG.h>
#include <TCanvas.h>
#include <TFile.h>

#include "fastjet/PseudoJet.hh"
#include "fastjet/ClusterSequenceArea.hh"
#ifndef __FJCORE__
#include "fastjet/GhostedAreaSpec.hh" // for area support
#endif                                // __FJCORE__

//______________________________________________________________________________
void LoadLibs()
{
  gSystem->Load("libfastjet");
  gSystem->Load("libsiscone");
  gSystem->Load("libsiscone_spherical");
  gSystem->Load("libfastjetplugins");

  gSystem->Load("libEG");
  //System->Load("libEGPythia8");
}

Double_t DistanceBetweenJets(fastjet::PseudoJet jet1, fastjet::PseudoJet jet2);
Bool_t IsJetOverlapping(fastjet::PseudoJet jet1, fastjet::PseudoJet jet2);
Bool_t IsBMeson(Int_t pc);
Bool_t IsDMeson(Int_t pc);

void RunPythia8(const char *inputfile = "pwgevents.lhe", Int_t nev = 25000, const char *foutname = "Pythia8JetSpectra.root", Int_t ndeb = 1)
{
  LoadLibs();
  clock_t begin_time = clock();

  TDatime dt;
  static UInt_t sseed = dt.Get();

  if (gSystem->Getenv("CONFIG_SEED"))
  {
    sseed = atoi(gSystem->Getenv("CONFIG_SEED"));
    std::cout << "\nseed for Random number generation is : " << sseed << std::endl;
  }

  const Int_t chargedOnly = 0; // charged only or full jets

  const Int_t nR = 5;
  const Float_t Rvals[nR] = {0.2, 0.3, 0.4, 0.5, 0.6}; // Cone radii
  //const Float_t Etavals[nR]={1.4,1.2,1.0,0.8,0.6}; //Eta range
  const Float_t Etavals[nR] = {1.0, 0.8, 0.6, 0.4, 0.2}; //Eta range EMCAL
  bool fDoPerpCone = kTRUE;

  TFile *fout = new TFile(foutname, "RECREATE");
  TH1F *hNEvent = new TH1F("hNEvent", "number of events; N", 1, 0, 1);
  TH1F *hJetPtSpecJet[nR] = {0};
  TH1F *hJetPtSpecSub[nR] = {0};
  TH1F *hBJetPtSpecJet[nR] = {0};
  TH1F *hBJetPtSpecSub[nR] = {0};
  TH1F *hCJetPtSpecJet[nR] = {0};
  TH1F *hCJetPtSpecSub[nR] = {0};

  for (Int_t iR = 0; iR < nR; iR++)
  {
    hJetPtSpecJet[iR] = new TH1F(Form("InclusiveJetXSection_R%.0f", 10 * Rvals[iR]),
                                 Form("Inclusive Jet Cross section R=%.1f;P_{T,Ch.jet}(Gev/c);d#sigma/dP_{T}d#eta(mb c/Gev)", Rvals[iR]),
                                 350, 0, 350);
    hJetPtSpecJet[iR]->Sumw2();

    hJetPtSpecSub[iR] = new TH1F(Form("BkgSubtractedJetXSection_R%.0f", 10 * Rvals[iR]),
                                 Form("Bkg Subtracted Jet Cross Section R=%.1f;P_{T,Ch.jet}(Gev/c);d#sigma/dP_{T}d#eta(mb c/Gev)", Rvals[iR]),
                                 400, -50, 350);
    hJetPtSpecSub[iR]->Sumw2();

    hBJetPtSpecJet[iR] = new TH1F(Form("BJetXSection_R%.0f", 10 * Rvals[iR]),
                                  Form("b-Jet Cross section R=%.1f;P_{T,Ch.jet}(Gev/c);d#sigma/dP_{T}d#eta(mb c/Gev)", Rvals[iR]),
                                  200, 0, 200);
    hBJetPtSpecJet[iR]->Sumw2();

    hBJetPtSpecSub[iR] = new TH1F(Form("BkgSubtractedBJetXSection_R%.0f", 10 * Rvals[iR]),
                                  Form("Bkg Subtracted b-Jet Cross Section R=%.1f;P_{T,Ch.jet}(Gev/c);d#sigma/dP_{T}d#eta(mb c/Gev)", Rvals[iR]),
                                  250, -50, 200);
    hBJetPtSpecSub[iR]->Sumw2();

    hCJetPtSpecJet[iR] = new TH1F(Form("CJetXSection_R%.0f", 10 * Rvals[iR]),
                                  Form("c-Jet Cross section R=%.1f;P_{T,Ch.jet}(Gev/c);d#sigma/dP_{T}d#eta(mb c/Gev)", Rvals[iR]),
                                  200, 0, 200);
    hCJetPtSpecJet[iR]->Sumw2();

    hCJetPtSpecSub[iR] = new TH1F(Form("BkgSubtractedCJetXSection_R%.0f", 10 * Rvals[iR]),
                                  Form("Bkg Subtracted c-Jet Cross Section R=%.1f;P_{T,Ch.jet}(Gev/c);d#sigma/dP_{T}d#eta(mb c/Gev)", Rvals[iR]),
                                  250, -50, 200);
    hCJetPtSpecSub[iR]->Sumw2();
  }

  // Array of particles
  TClonesArray *particles = new TClonesArray("TParticle", 1000);
  // Create pythia8 object
  TPythia8 *pythia8 = new TPythia8();

  std::vector<fastjet::JetDefinition> jet_def;
  std::vector<fastjet::JetDefinition> jet_defBkg;
  Double_t ghost_maxrap = 6.0;
  fastjet::GhostedAreaSpec area_spec(ghost_maxrap);
  fastjet::AreaDefinition area_def(fastjet::active_area, area_spec);

  for (Int_t iR = 0; iR < nR; iR++)
    jet_def.push_back(fastjet::JetDefinition(fastjet::antikt_algorithm, Rvals[iR]));

  for (Int_t iR = 0; iR < nR; iR++)
    jet_defBkg.push_back(fastjet::JetDefinition(fastjet::kt_algorithm, Rvals[iR]));

  // Configure
  pythia8->ReadString("Next:numberShowLHA = 1");
  pythia8->ReadString("Next:numberShowInfo = 1");
  pythia8->ReadString("Next:numberShowProcess = 1");
  pythia8->ReadString("Next:numberShowEvent = 1");
  pythia8->ReadString("Main:timesAllowErrors = 10");

  pythia8->ReadString("Init:showChangedSettings = on");
  pythia8->ReadString("Init:showChangedParticleData = off");

  // In oreder to Read .lhe file
  pythia8->ReadString("Beams:frametype = 4");

  pythia8->ReadString(Form("Beams:LHEF = %s", inputfile));

  pythia8->ReadString("POWHEG:nFinal = 2");

  //pythia8->ReadString("PartonLevel:MPI = on"); //! TEST

  // Switch On Pi0 Decay
  pythia8->ReadString("111:mayDecay  = on");
  pythia8->ReadString("310:mayDecay  = off");
  pythia8->ReadString("3122:mayDecay = off");
  pythia8->ReadString("3112:mayDecay = off");
  pythia8->ReadString("3212:mayDecay = off");
  pythia8->ReadString("3222:mayDecay = off");
  pythia8->ReadString("3312:mayDecay = off");
  pythia8->ReadString("3322:mayDecay = off");
  pythia8->ReadString("3334:mayDecay = off");

  // POWHEG Merging Parameters
  pythia8->ReadString("POWHEG:veto = 1");
  pythia8->ReadString("POWHEG:vetoCount = 10000");
  pythia8->ReadString("POWHEG:pThard = 2");  //! Effective
  pythia8->ReadString("POWHEG:pTemt = 0");   // Don't Change this parameter
  pythia8->ReadString("POWHEG:emitted = 0"); //!
  pythia8->ReadString("POWHEG:pTdef = 1");   //! Effective
  pythia8->ReadString("POWHEG:MPIveto = 0");
  pythia8->ReadString("POWHEG:QEDveto = 2");

  // Tune Parameters
  pythia8->ReadString("Tune:preferLHAPDF = 2");
  pythia8->ReadString("Tune:pp = 21"); //Tune 4C

  // PDF Selection
  //pythia8->ReadString("PDF:pSet = LHAPDF6:cteq66");
  //pythia8->ReadString("PDF:nPDFBeamB = 100822080");
  //pythia8->ReadString("PDF:pSetB = LHAPDF6:EPPS16nlo_CT14nlo_Pb208");
  //pythia8->ReadString("PDF:useHardNPDFB = on");
  //pythia8->ReadString("PDF:nPDFSetB = 2");

  // Random Seed
  pythia8->ReadString("Random:setSeed = on");
  pythia8->ReadString(Form("Random:seed = %u", sseed % 900000000));

  //
  Pythia8::Pythia *pythia = pythia8->Pythia8();

  Int_t MPIvetoMode = pythia->settings.mode("POWHEG:MPIveto");

  // Add in user hooks for shower vetoing
  Pythia8::PowhegHooks *powhegHooks = NULL;
  pythia->readString("SpaceShower:pTmaxMatch = 2");
  pythia->readString("TimeShower:pTmaxMatch = 2");

  if (MPIvetoMode > 0)
  {
    pythia->readString("MultipartonInteractions:pTmaxMatch = 2");
  }

  // Set User Hooks
  powhegHooks = new Pythia8::PowhegHooks();
  pythia->setUserHooksPtr((std::shared_ptr<Pythia8::UserHooks>)powhegHooks);

  TString PDFused = pythia->settings.word("PDF:pSet");
  std::cout << "\n PDF used is : " << PDFused << std::endl;
  Double_t SumW(0);

  // Initialize
  pythia->init();
  //

  // Event loop
  for (Int_t iev = 0; iev < nev; iev++)
  {

    if (!(iev % 1000))
    {
      printf(">>>processing ev# %5d / elapsed time: ", iev);
      std::cout << float(clock() - begin_time) / CLOCKS_PER_SEC << std::endl;
      begin_time = clock();
    }

    std::vector<fastjet::PseudoJet> input_particles;
    std::vector<fastjet::PseudoJet> bPartons;
    std::vector<fastjet::PseudoJet> cPartons;

    //vector<fastjet::PseudoJet> bHadrons;
    //vector<fastjet::PseudoJet> cHadrons;

    pythia8->GenerateEvent();
    // pythia8->EventListing();
    pythia8->ImportParticles(particles, "All");

    Double_t evt_wght = pythia->info.weight(); //Event Weight for weighted events
    evt_wght *= 1e-9;                          // Weight is pb so *1e-9 to transform to mb

    SumW += evt_wght;

    hNEvent->Fill(0.5);

    Int_t np = particles->GetEntriesFast();

    // Particle loop
    Int_t Ipsb[3] = {-1, -1, -1}, ib(0);
    Int_t Ipsc[3] = {-1, -1, -1}, ic(0);
    for (Int_t ip = 0; ip < pythia8->Pythia8()->event.size(); ip++)
    {

      Pythia8::Particle part = pythia8->Pythia8()->event[ip];

      //Parton Definition
      //if((part.status() == -23 ||part.status() == -24) && (part.id() == 4 || part.id()==-4) ){
      //if((part.status() == -23 ||part.status() == -24) && (part.id() == 5 || part.id()==-5) ){
      if ((part.id() == 5 || part.id() == -5))
      {
        bPartons.push_back(fastjet::PseudoJet(part.px(), part.py(), part.pz(), part.e()));
        //std::cout<<"The partices status is :"<<part.status()<<" And the PDG code is :"<<part.id()<<" And the Eta is :"<<part.eta()<<" And Phi is :"<<part.phi()<<" and its PT is:"<<part.pT()<<endl;
        //Ipsb[ib] = ip; ib++;
      }
      else if ((part.id() == 4 || part.id() == -4))
      {
        cPartons.push_back(fastjet::PseudoJet(part.px(), part.py(), part.pz(), part.e()));
        //std::cout<<"The partices status is :"<<part.status()<<" And the PDG code is :"<<part.id()<<" And the Eta is :"<<part.eta()<<" And Phi is :"<<part.phi()<<" and its PT is:"<<part.pT()<<endl;
        //Ipsc[ic] = ip; ic++;
      }

      /*if(abs(part.eta())>0.9 || part.pT()<0.15) continue;
 
	//Hadron Definition
	if( IsDMeson(part.id()) ){
		for(unsigned int cquark=0; cquark<cPartons.size(); cquark++){

			Double_t DeltaEta = TMath::Abs(part.eta() - cPartons[cquark].eta());
			Double_t DeltaPhi = TVector2::Phi_mpi_pi((part.phi() - cPartons[cquark].phi()));
			Double_t DeltaR = TMath::Sqrt(DeltaPhi*DeltaPhi + DeltaEta*DeltaEta);

		   if(DeltaR < 0.1 ){
			cout<<"this particle is from c quark"<<endl; 
		   }
		}
	        cPartons.push_back(fastjet::PseudoJet(part.px(), part.py(), part.pz(), part.e())); 
	}

	if( IsBMeson(part.id()) ){
		for(unsigned int bquark=0; bquark<bPartons.size(); bquark++){

			Double_t DeltaEta = TMath::Abs(part.eta() - bPartons[bquark].eta());
			Double_t DeltaPhi = TVector2::Phi_mpi_pi((part.phi() - bPartons[bquark].phi()));
			Double_t DeltaR = TMath::Sqrt(DeltaPhi*DeltaPhi + DeltaEta*DeltaEta);

		   if(DeltaR < 0.1 ){
			cout<<"this particle is from b quark"<<endl; 
		   }
		}
	        bPartons.push_back(fastjet::PseudoJet(part.px(), part.py(), part.pz(), part.e())); 
	}*/

      //Track Definition
      /*if(part.isFinal()){

		if(abs(part.eta())>0.9 || part.pT()<0.15) continue;

		if(pythia8->Pythia8()->event[ip].isAncestor(Ipsb[0]) || pythia8->Pythia8()->event[ip].isAncestor(Ipsb[1]) || pythia8->Pythia8()->event[ip].isAncestor(Ipsb[2])){
			cout<<"this particle is from b quark"<<endl; 
	        	bPartons.push_back(fastjet::PseudoJet(part.px(), part.py(), part.pz(), part.e())); 
		}

		if(pythia8->Pythia8()->event[ip].isAncestor(Ipsc[0]) || pythia8->Pythia8()->event[ip].isAncestor(Ipsc[1]) || pythia8->Pythia8()->event[ip].isAncestor(Ipsc[2])){
			cout<<"this particle is from c quark"<<endl; 
	        	cPartons.push_back(fastjet::PseudoJet(part.px(), part.py(), part.pz(), part.e())); 
		}
		
        }*/
    }

    for (Int_t ip = 0; ip < np; ip++)
    {
      TParticle *part = (TParticle *)particles->At(ip);
      Int_t ist = part->GetStatusCode();

      // Positive codes are final particles.
      if (ist <= 0)
        continue;

      Int_t pdg = part->GetPdgCode();
      Float_t charge = TDatabasePDG::Instance()->GetParticle(pdg)->Charge();

      if (chargedOnly)
      {
        if (charge == 0.)
          continue; //charged particles only
      }
      else
      {
        if (part->GetPdgCode() == 12 || part->GetPdgCode() == 14 || part->GetPdgCode() == 16) // reject neutrinos
          continue;
      }

      Float_t eta = part->Eta();
      Float_t pt = part->Pt();

      //if (abs(eta) > 0.9)
      if (abs(eta) > 0.7)
        continue;
      // if (pt < 0.15)
      //   continue;

      input_particles.push_back(fastjet::PseudoJet(part->Px(), part->Py(), part->Pz(), part->Energy()));
    }

    if (input_particles.size() == 0)
    {
      //printf("No particle....\n");
      continue;
    }

    for (Int_t iR = 0; iR < nR; iR++)
    {

      Double_t AreaCut = 0.6 * TMath::Pi() * TMath::Power(Rvals[iR], 2);

      fastjet::ClusterSequenceArea clust_seq(input_particles, jet_def[iR], area_def);
      double ptmin = 1.0;
      std::vector<fastjet::PseudoJet> inclusive_jets = sorted_by_pt(clust_seq.inclusive_jets(ptmin));

      fastjet::ClusterSequenceArea clust_seqBkg(input_particles, jet_defBkg[iR], area_def);
      std::vector<fastjet::PseudoJet> inclusive_jetsBkg = sorted_by_pt(clust_seqBkg.inclusive_jets(0.));

      if (inclusive_jets.size() == 0)
        continue;

      Double_t Rho = 0.;

      // Perp Cone for underlying Event Subtraction
      if (fDoPerpCone)
      {
        Double_t PerpConePhi = inclusive_jets[0].phi() + TMath::Pi() / 2;
        PerpConePhi = (PerpConePhi > 2 * TMath::Pi()) ? PerpConePhi - 2 * TMath::Pi() : PerpConePhi; // fit to 0 < phi < 2pi

        Double_t PerpConeEta = inclusive_jets[0].eta();
        Double_t PerpConePt(0);

        for (unsigned int j = 0; j < input_particles.size(); j++)
        {

          Double_t deltaR(0);

          Double_t dPhi = TMath::Abs(input_particles[j].phi() - PerpConePhi);
          dPhi = (dPhi > TMath::Pi()) ? 2 * TMath::Pi() - dPhi : dPhi;

          Double_t dEta = TMath::Abs(input_particles[j].eta() - PerpConeEta);

          deltaR = TMath::Sqrt(TMath::Power(dEta, 2) + TMath::Power(dPhi, 2));

          if (deltaR <= Rvals[iR])
            PerpConePt += input_particles[j].pt();
        }

        Double_t PerpConeRho = PerpConePt / (TMath::Pi() * TMath::Power(Rvals[iR], 2));
        Rho = PerpConeRho;
      }
      else
      {
        // Rho Sparse for underlying Event Subtraction
        static Double_t rhovec[999];
        Int_t NjetAcc = 0;
        Double_t TotaljetAreaPhys = 0;
        Double_t TotalTPCArea = 2 * TMath::Pi() * 0.9;

        // push all jets within selected acceptance into stack
        for (unsigned int iJets = 0; iJets < inclusive_jetsBkg.size(); ++iJets)
        {

          // exlcuding leading background jets (could be signal)
          if (iJets == 0 || iJets == 1)
            continue;

          if (TMath::Abs(inclusive_jetsBkg[iJets].eta()) > (0.5))
            continue;

          // Search for overlap with signal jets
          Bool_t isOverlapping = kFALSE;
          if (inclusive_jets.size() > 0)
          {
            for (unsigned int j = 0; j < inclusive_jets.size(); j++)
            {
              if (inclusive_jets[j].perp() < 5)
                continue;

              if (IsJetOverlapping(inclusive_jets[j], inclusive_jetsBkg[iJets]))
              {
                isOverlapping = kTRUE;
                break;
              }
            }
          }
          if (isOverlapping)
            continue;

          //This is to exclude pure ghost jets from the rho calculation
          std::vector<fastjet::PseudoJet> ContJet = inclusive_jetsBkg[iJets].constituents();
          if (ContJet.size() > 0)
          {
            TotaljetAreaPhys += inclusive_jetsBkg[iJets].area();
            rhovec[NjetAcc] = inclusive_jetsBkg[iJets].perp() / inclusive_jetsBkg[iJets].area();
            ++NjetAcc;
          }
        }

        Double_t OccCorr = TotaljetAreaPhys / TotalTPCArea;

        Double_t rho = 0.;

        if (NjetAcc > 0)
        {
          //find median value
          rho = TMath::Median(NjetAcc, rhovec);
          rho = rho * OccCorr;
        }
        Rho = rho;
      }

      for (unsigned int i = 0; i < inclusive_jets.size(); i++)
      {

        if (TMath::Abs(inclusive_jets[i].eta()) > (Etavals[iR] / 2))
          continue;

        Double_t PtSub = inclusive_jets[i].perp() - (Rho * inclusive_jets[i].area());

        hJetPtSpecJet[iR]->Fill(inclusive_jets[i].perp(), evt_wght);
        hJetPtSpecSub[iR]->Fill(PtSub, evt_wght);

        //b-jet
        for (unsigned int bjet = 0; bjet < bPartons.size(); bjet++)
        {
          Double_t DeltaR = DistanceBetweenJets(inclusive_jets[i], bPartons[bjet]);
          //cout<<"The distance for R="<<Rvals[iR]<<" is :"<<DeltaR<<" And the jet Eta is:"<<inclusive_jets[i].eta()<<" and the Phi is :"<<inclusive_jets[i].phi()<<endl;
          if (DeltaR < (Rvals[iR]))
          {
            hBJetPtSpecJet[iR]->Fill(inclusive_jets[i].perp(), evt_wght);
            hBJetPtSpecSub[iR]->Fill(PtSub, evt_wght);
            //cout<<"This is a b-jet "<<endl;
            break;
          }
        }

        //c-jet
        for (unsigned int cjet = 0; cjet < cPartons.size(); cjet++)
        {
          Double_t DeltaR = DistanceBetweenJets(inclusive_jets[i], cPartons[cjet]);
          //cout<<"The distance for R="<<Rvals[iR]<<" is :"<<DeltaR<<" And the jet Eta is:"<<inclusive_jets[i].eta()<<" and the Phi is :"<<inclusive_jets[i].phi()<<endl;
          if (DeltaR < (Rvals[iR]))
          {
            hCJetPtSpecJet[iR]->Fill(inclusive_jets[i].perp(), evt_wght);
            hCJetPtSpecSub[iR]->Fill(PtSub, evt_wght);
            //cout<<"This is a c-jet "<<endl;
            break;
          }
        }
      }
    }
  }

  pythia8->PrintStatistics();

  Double_t sumw = pythia->info.weightSum();
  //sumw *= 1e-9;
  Double_t TotalXSec = pythia->info.sigmaGen();

  std::cout << "\nTotal Xsec is : " << TotalXSec << "  Total Weight is : " << sumw << "          " << SumW << std::endl;

  TProfile *CrossSection = new TProfile("CrossSection", "Total cross section", 1, 0, 1);
  CrossSection->Fill(0.5, TotalXSec);

  TH1D *NumberofTrials = new TH1D("NumberofTrials", "Number of Trials", 1, 0, 1);
  NumberofTrials->SetBinContent(1, sumw);

  //Normalization
  /*for (int iR = 0; iR < nR; iR++){
    
     hJetPtSpecJet[iR]->Scale( (TotalXSec/sumw));
     hJetPtSpecSub[iR]->Scale( (TotalXSec/sumw));
     hBJetPtSpecJet[iR]->Scale( (TotalXSec/sumw));
     hBJetPtSpecSub[iR]->Scale( (TotalXSec/sumw));
     hCJetPtSpecJet[iR]->Scale( (TotalXSec/sumw));
     hCJetPtSpecSub[iR]->Scale( (TotalXSec/sumw));
	//In case of non Weighted Events you should normalize by  TotalXSec/sumw instead of (1.0/nev)

  }*/

  fout->Write();
} //
// //
//________________________________________________________________________
Double_t DistanceBetweenJets(fastjet::PseudoJet jet1, fastjet::PseudoJet jet2)
{

  Double_t DeltaEta = TMath::Abs(jet1.eta() - jet2.eta());
  Double_t DeltaPhi = TVector2::Phi_mpi_pi((jet1.phi() - jet2.phi()));

  Double_t DeltaR = TMath::Sqrt(DeltaPhi * DeltaPhi + DeltaEta * DeltaEta);

  return DeltaR;
}
//________________________________________________________________________
Bool_t IsBMeson(Int_t pc)
{
  int bPdG[] = {511, 521, 10511, 10521, 513, 523, 10513, 10523, 20513, 20523, 20513, 20523, 515, 525, 531,
                10531, 533, 10533, 20533, 535, 541, 10541, 543, 10543, 20543, 545, 551, 10551, 100551,
                110551, 200551, 210551, 553, 10553, 20553, 30553, 100553, 110553, 120553, 130553, 200553, 210553, 220553,
                300553, 9000533, 9010553, 555, 10555, 20555, 100555, 110555, 120555, 200555, 557, 100557, 5122, 5112, 5212, 5222, 5114, 5214, 5224, 5132, 5232, 5312, 5322, 5314, 5324, 5332, 5334, 5142, 5242, 5412, 5422, 5414, 5424, 5342, 5432, 5434, 5442, 5444, 5512, 5522, 5514, 5524, 5532,
                5534, 5542, 5544, 5554};
  for (int i = 0; i < (int)(sizeof(bPdG) / sizeof(int)); ++i)
    if (abs(pc) == bPdG[i])
      return true;
  return false;
}
//________________________________________________________________________
Bool_t IsDMeson(Int_t pc)
{
  int bPdG[] = {411, 421, 10411, 10421, 413, 423, 10413, 10423, 20431, 20423, 415,
                425, 431, 10431, 433, 10433, 20433, 435, 441, 10441, 100441, 443, 10443, 20443,
                100443, 30443, 9000443, 9010443, 9020443, 445, 100445, 4122, 4222, 4212, 4112, 4224, 4214, 4114, 4232, 4132, 4322, 4312, 4324, 4314, 4332, 4334, 4412, 4422, 4414, 4424, 4432, 4434, 4444};
  for (int i = 0; i < (int)(sizeof(bPdG) / sizeof(int)); ++i)
    if (abs(pc) == bPdG[i])
      return true;
  return false;
}
//________________________________________________________________________
Bool_t IsJetOverlapping(fastjet::PseudoJet jet1, fastjet::PseudoJet jet2)
{

  std::vector<fastjet::PseudoJet> ContJet1 = jet1.constituents();
  std::vector<fastjet::PseudoJet> ContJet2 = jet2.constituents();

  for (unsigned int i = 0; i < ContJet1.size(); ++i)
  {
    //Int_t jet1Track = jet1->TrackAt(i);
    for (unsigned int j = 0; j < ContJet2.size(); ++j)
    {
      //Int_t jet2Track = jet2->TrackAt(j);
      if ((ContJet1[i].perp() == ContJet2[j].perp()) && (ContJet1[i].phi() == ContJet2[j].phi()) && (ContJet1[i].eta() == ContJet2[j].eta()))
        return kTRUE;
    }
  }
  return kFALSE;
}
