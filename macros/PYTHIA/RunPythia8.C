#ifdef __CLING__
R__LOAD_LIBRARY(libpythia8.so)
R__ADD_INCLUDE_PATH($PYTHIA_ROOT/include)
#endif
#include "Pythia8/Pythia.h"
#include "Pythia8Plugins/PowhegHooks.h"
#include "Pythia8/ParticleData.h"

#ifndef __CLING__
#include <memory>
#include <TROOT.h>
#include <TSystem.h>
#include <TH1F.h>
#include <TProfile.h>
#include <TClonesArray.h>
#include <TParticle.h>
#include <TDatabasePDG.h>
#include <TCanvas.h>
#include <TFile.h>
#endif

#ifdef __CLING__
R__LOAD_LIBRARY(libfastjet)
R__LOAD_LIBRARY(libsiscone)
R__LOAD_LIBRARY(libsiscone_spherical)
R__LOAD_LIBRARY(libfastjetplugins)
R__ADD_INCLUDE_PATH($FASTJET_ROOT/include)
#endif
#include "fastjet/PseudoJet.hh"
#include "fastjet/ClusterSequenceArea.hh"
#ifndef __FJCORE__
#include "fastjet/GhostedAreaSpec.hh" // for area support
#endif                                // __FJCORE__

Double_t DistanceBetweenJets(fastjet::PseudoJet jet1, fastjet::PseudoJet jet2);
Bool_t IsJetOverlapping(fastjet::PseudoJet jet1, fastjet::PseudoJet jet2);
Bool_t IsBMeson(Int_t pc);
Bool_t IsDMeson(Int_t pc);

class PythiaHandler {
public:
    PythiaHandler() : mEngine(), mPDFset("default"), mTune(21), mWithMPI(false), mDecay(false), mOutput(nullptr){}
    ~PythiaHandler(){}

    void configure(const char *inputfile, unsigned long seed){
        // Configure
        mEngine.readString("Next:numberShowLHA = 1");
        mEngine.readString("Next:numberShowInfo = 1");
        mEngine.readString("Next:numberShowProcess = 1");
        mEngine.readString("Next:numberShowEvent = 1");
        mEngine.readString("Main:timesAllowErrors = 10");

        mEngine.readString("Init:showChangedSettings = on");
        mEngine.readString("Init:showChangedParticleData = off");

        // In oreder to Read .lhe file
        mEngine.readString("Beams:frametype = 4");

        mEngine.readString(Form("Beams:LHEF = %s", inputfile));

        mEngine.readString("POWHEG:nFinal = 2");

        if(mWithMPI){
            mEngine.readString("PartonLevel:MPI = on"); //! TEST
        }

        // Switch On Pi0 Decay
        mEngine.readString("111:mayDecay  = on");
        if(!mDecay) {
            mEngine.readString("310:mayDecay  = off");
            mEngine.readString("3122:mayDecay = off");
            mEngine.readString("3112:mayDecay = off");
            mEngine.readString("3212:mayDecay = off");
            mEngine.readString("3222:mayDecay = off");
            mEngine.readString("3312:mayDecay = off");
            mEngine.readString("3322:mayDecay = off");
            mEngine.readString("3334:mayDecay = off");
        }

        // POWHEG Merging Parameters
        mEngine.readString("POWHEG:veto = 1");
        mEngine.readString("POWHEG:vetoCount = 10000");
        mEngine.readString("POWHEG:pThard = 2");  //! Effective
        mEngine.readString("POWHEG:pTemt = 0");   // Don't Change this parameter
        mEngine.readString("POWHEG:emitted = 0"); //!
        mEngine.readString("POWHEG:pTdef = 1");   //! Effective
        mEngine.readString("POWHEG:MPIveto = 0");
        mEngine.readString("POWHEG:QEDveto = 2");

        // Tune Parameters
        mEngine.readString("Tune:preferLHAPDF = 2");
        mEngine.readString(Form("Tune:pp = %d", mTune)); //Tune 4C

        // PDF Selection
        if(mPDFset != "default") {
            mEngine.readString(Form("PDF:pSet = LHAPDF6:%s", mPDFset.c_str()));
        }
        //pythia8->ReadString("PDF:nPDFBeamB = 100822080");
        //pythia8->ReadString("PDF:pSetB = LHAPDF6:EPPS16nlo_CT14nlo_Pb208");
        //pythia8->ReadString("PDF:useHardNPDFB = on");
        //pythia8->ReadString("PDF:nPDFSetB = 2");

        // Random Seed
        mEngine.readString("Random:setSeed = on");
        mEngine.readString(Form("Random:seed = %lu", seed % 900000000));

        // Add in user hooks for shower vetoing
        mEngine.readString("SpaceShower:pTmaxMatch = 2");
        mEngine.readString("TimeShower:pTmaxMatch = 2");


        Int_t MPIvetoMode = mEngine.settings.mode("POWHEG:MPIveto");
        if (MPIvetoMode > 0) {
            mEngine.readString("MultipartonInteractions:pTmaxMatch = 2");
        }

        // Set User Hooks
        mPowhegHooks = std::make_shared<Pythia8::PowhegHooks>();
        mEngine.setUserHooksPtr(mPowhegHooks);
    }

    void init() { mEngine.init(); }

    void setOutput(TClonesArray *output) { mOutput = output; }

    void setPDFset(const char *pdfset) { mPDFset = pdfset; }

    void setTune(int tune) { mTune = tune; }

    void setDecay() { mDecay = true; }

    void setMPI() {mWithMPI = true;}
  
    Pythia8::Pythia &getEngine() { return mEngine; }

    bool generate() {
        mOutput->Clear();
        return mEngine.next();
    }

    int importParticles(Option_t *option){
        if (!mOutput ) return 0;
        TClonesArray &clonesParticles = *mOutput;
        clonesParticles.Clear();
        Int_t nparts=0;
        Int_t ioff = 0;
        if (mEngine.event[0].id() == 90) {
            ioff = -1;
        }

        bool selectFinal = !strcmp(option,"") || !strcmp(option,"Final"),
             selectAll = !strcmp(option,"All");
  
        for (int i = 0; i < mEngine.event.size(); i++) {
            if (mEngine.event[i].id() == 90) continue;
            if (selectFinal && !mEngine.event[i].isFinal()) continue;
            new(clonesParticles[nparts]) TParticle(
                                                    mEngine.event[i].id(),
                                                    mEngine.event[i].isFinal(),
                                                    mEngine.event[i].mother1() + ioff,
                                                    mEngine.event[i].mother2() + ioff,
                                                    mEngine.event[i].daughter1() + ioff,
                                                    mEngine.event[i].daughter2() + ioff,
                                                    mEngine.event[i].px(),     // [GeV/c]
                                                    mEngine.event[i].py(),     // [GeV/c]
                                                    mEngine.event[i].pz(),     // [GeV/c]
                                                    mEngine.event[i].e(),      // [GeV]
                                                    mEngine.event[i].xProd(),  // [mm]
                                                    mEngine.event[i].yProd(),  // [mm]
                                                    mEngine.event[i].zProd(),  // [mm]
                                                    mEngine.event[i].tProd()); // [mm/c]
            nparts++;
        } // final state partice
        return nparts;
    }

private:
    Pythia8::Pythia mEngine;
    std::string mPDFset;
    int mTune;
    bool mWithMPI;
    bool mDecay;
    std::shared_ptr<Pythia8::PowhegHooks> mPowhegHooks;
    TClonesArray *mOutput;
};  

void RunPythia8(const char *inputfile = "pwgevents.lhe", const char *foutname = "Pythia8JetSpectra.root", Int_t ndeb = 1) {
    clock_t begin_time = clock();

    const double MBtoPB = 1e-9;
    const double kMaxEta = 0.7;

    TDatime dt;
    static UInt_t sseed = dt.Get();

    if (gSystem->Getenv("CONFIG_SEED")) {
        sseed = atoi(gSystem->Getenv("CONFIG_SEED"));
        std::cout << "\nseed for Random number generation is : " << sseed << std::endl;
    }

    Int_t chargedOnly = 0; // charged only or full jets

    const Int_t nR = 5;
    const Float_t Rvals[nR] = {0.2, 0.3, 0.4, 0.5, 0.6}; // Cone radii
    //const Float_t Etavals[nR]={1.4,1.2,1.0,0.8,0.6}; //Eta range
    const Float_t Etavals[nR] = {1.0, 0.8, 0.6, 0.4, 0.2}; //Eta range EMCAL
    bool fDoPerpCone = kTRUE;

    std::unique_ptr<TFile> fout(TFile::Open(foutname, "RECREATE"));
    TH1F *hNEvent = new TH1F("hNEvent", "number of events; N", 1, 0, 1);
    std::array<TH1 *, nR> hJetPtSpecJet, hJetPtSpecSub, hBJetPtSpecJet, hBJetPtSpecSub, hCJetPtSpecJet, hCJetPtSpecSub;

    for (Int_t iR = 0; iR < nR; iR++) {
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
    PythiaHandler pythia;
    if(gSystem->Getenv("CONFIG_PDFSET")) {
        std::string pdfset = gSystem->Getenv("CONFIG_PDFSET");
        std::cout << "Setting pdfset: " << pdfset;
        pythia.setPDFset(pdfset.c_str());    
    }
    if(gSystem->Getenv("CONFIG_TUNE")) {
        int tune = atoi(gSystem->Getenv("CONFIG_TUNE"));
        std::cout << "Setting tune: " << tune << std::endl;
        pythia.setTune(tune);    
    }
    if(gSystem->Getenv("CONFIG_MPI")) {
        int val = atoi(gSystem->Getenv("CONFIG_MPI"));
        if(val > 0) {
            std::cout << "Setting MPI" << std::endl;
            pythia.setMPI();
        } 
    }
    if(gSystem->Getenv("CONFIG_DECAY")) {
        int val = atoi(gSystem->Getenv("CONFIG_DECAY"));
        if(val > 0) {
            std::cout << "Setting Decays" << std::endl;
            pythia.setDecay();
        } 
    }
    if(gSystem->Getenv("CONFIG_JETTYPE")) {
        int val = atoi(gSystem->Getenv("CONFIG_JETTYPE"));
        if(val == 1) {
            std::cout << "Setting full jets" << std::endl;
            chargedOnly = 0;
        } else {
            std::cout << "Setting charged jets" << std::endl;
            chargedOnly = 1;
        } 
    }
    double ptcutCharged=0., ptcutNeutral=0., ecutCharged = 0., ecutNeutral=0.;
    if(gSystem->Getenv("CONFIG_PTCUT")) {
        float val = atof(gSystem->Getenv("CONFIG_PTCUT"));
        if(val > 0) {
            std::cout << "Applying same ptcut on charged and neutral particles: "  << val << " MeV/c"  << std::endl;
            ptcutCharged = val / 1000.;
            ptcutNeutral = val / 1000.;
        } else {
            std::cout << "Applying std. ptcuts: 150 MeV/c (charged), 300 MeV/c (neutra)" << std::endl;
            ptcutCharged = 0.15;
            ptcutNeutral = 0.3;
        }
    }
    if(gSystem->Getenv("CONFIG_CHPTCUT")) {
        float val = atof(gSystem->Getenv("CONFIG_CHPTCUT"));
        if(val > 0) {
            std::cout << "Applying ptcut on charged particles: "  << val << " MeV/c"  << std::endl;
            ptcutCharged = val / 1000.;
        } else {
            std::cout << "Applying std. ptcut charged particles: 150 MeV/c" << std::endl;
            ptcutCharged = 0.15;
        }
    }
    if(gSystem->Getenv("CONFIG_NEPTCUT")) {
        float val = atof(gSystem->Getenv("CONFIG_NEPTCUT"));
        if(val > 0) {
            std::cout << "Applying ptcut on neutral particles: "  << val << " MeV/c"  << std::endl;
            ptcutNeutral = val / 1000.;
        } else {
            std::cout << "Applying std. ptcut neutral particles: 300 MeV/c" << std::endl;
            ptcutNeutral = 0.3;
        }
    }
    if(gSystem->Getenv("CONFIG_ECUT")) {
        float val = atof(gSystem->Getenv("CONFIG_ECUT"));
        if(val > 0) {
            std::cout << "Applying same energy cut on charged and neutral particles: "  << val << " MeV"  << std::endl;
            ecutCharged = val / 1000.;
            ecutNeutral = val / 1000.;
        } else {
            std::cout << "Applying std. energy cuts: 150 MeV/c (charged), 300 MeV/c (neutra)" << std::endl;
            ecutCharged = 0.15;
            ecutNeutral = 0.3;
        }
    }
    if(gSystem->Getenv("CONFIG_CHECUT")) {
        float val = atof(gSystem->Getenv("CONFIG_CHECUT"));
        if(val > 0) {
            std::cout << "Applying energy cut on charged particles: "  << val << " MeV"  << std::endl;
            ecutCharged = val / 1000.;
        } else {
            std::cout << "Applying std. energy cut charged particles: 150 MeV" << std::endl;
            ecutCharged = 0.15;
        }
    }
    if(gSystem->Getenv("CONFIG_NEECUT")) {
        float val = atof(gSystem->Getenv("CONFIG_NEECUT"));
        if(val > 0) {
            std::cout << "Applying energy cut on neutral particles: "  << val << " MeV/c"  << std::endl;
            ecutNeutral = val / 1000.;
        } else {
            std::cout << "Applying std. energy cut neutral particles: 300 MeV/c" << std::endl;
            ecutNeutral = 0.3;
        }
    }
    fastjet::RecombinationScheme scheme = fastjet::E_scheme;
    if(gSystem->Getenv("CONFIG_RECOMBINATIONSCHEME")) {
        std::string value = gSystem->Getenv("CONFIG_RECOMBINATIONSCHEME");
        std::cout << "Setting recombination scheme to " << value;
        if(value == "Escheme") {
            scheme = fastjet::E_scheme;
        } else if(value == "ptscheme") {
            scheme = fastjet::pt_scheme;
        } else if(value == "pt2scheme") {
            scheme = fastjet::pt2_scheme;
        } else if(value == "Etscheme") {
            scheme = fastjet::Et_scheme;
        } else if(value == "Et2scheme") {
            scheme = fastjet::Et2_scheme;
        } else {
            std::cerr << "Unknown recombination scheme, exiting" << std::endl;
            return;
        }
    }
    pythia.configure(inputfile, sseed);
    pythia.setOutput(particles);
    auto &engine = pythia.getEngine();

    std::vector<fastjet::JetDefinition> jet_def;
    std::vector<fastjet::JetDefinition> jet_defBkg;
    Double_t ghost_maxrap = 6.0;
    fastjet::GhostedAreaSpec area_spec(ghost_maxrap);
    fastjet::AreaDefinition area_def(fastjet::active_area, area_spec);

    for (Int_t iR = 0; iR < nR; iR++)
        jet_def.push_back(fastjet::JetDefinition(fastjet::antikt_algorithm, Rvals[iR], scheme));

    for (Int_t iR = 0; iR < nR; iR++)
        jet_defBkg.push_back(fastjet::JetDefinition(fastjet::kt_algorithm, Rvals[iR], scheme));


    TString PDFused = engine.settings.word("PDF:pSet");
    std::cout << "\n PDF used is : " << PDFused << std::endl;
    Double_t SumW(0);

    // Initialize
    pythia.init();
    //

    // Event loop
    int iev = 0;
    while(true) {

        if (!(iev % 1000)) {
            printf(">>>processing ev# %5d / elapsed time: ", iev);
            std::cout << float(clock() - begin_time) / CLOCKS_PER_SEC << std::endl;
            begin_time = clock();
        }

        std::vector<fastjet::PseudoJet> input_particles;
        std::vector<fastjet::PseudoJet> bPartons;
        std::vector<fastjet::PseudoJet> cPartons;

        //std::vector<fastjet::PseudoJet> bHadrons;
        //std::vector<fastjet::PseudoJet> cHadrons;

        if(!pythia.generate()) {
            std::cout << "No more events ...";
            break;
        }   
        pythia.importParticles("All");

        Double_t evt_wght = engine.info.weight(); //Event Weight for weighted events
        evt_wght *= MBtoPB;                       // Weight is pb so *1e-9 to transform to mb

        SumW += evt_wght;

        hNEvent->Fill(0.5);

        Int_t np = particles->GetEntriesFast();

        // Particle loop
        Int_t Ipsb[3] = {-1, -1, -1}, ib(0);
        Int_t Ipsc[3] = {-1, -1, -1}, ic(0);
        for (Int_t ip = 0; ip < engine.event.size(); ip++) {

            Pythia8::Particle part = engine.event[ip];

            //Parton Definition
            //if((part.status() == -23 ||part.status() == -24) && (part.id() == 4 || part.id()==-4) ){
            //if((part.status() == -23 ||part.status() == -24) && (part.id() == 5 || part.id()==-5) ){
            if ((part.id() == 5 || part.id() == -5)) {
                bPartons.push_back(fastjet::PseudoJet(part.px(), part.py(), part.pz(), part.e()));
                //std::cout<<"The partices status is :"<<part.status()<<" And the PDG code is :"<<part.id()<<" And the Eta is :"<<part.eta()<<" And Phi is :"<<part.phi()<<" and its PT is:"<<part.pT()<<endl;
                //Ipsb[ib] = ip; ib++;
            } else if ((part.id() == 4 || part.id() == -4)) {
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
        			    std::cout<<"this particle is from c quark"<<std::endl; 
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
			            std::cout<<"this particle is from b quark"<<::endl; 
		            }
		        }
	            bPartons.push_back(fastjet::PseudoJet(part.px(), part.py(), part.pz(), part.e())); 
	        }*/

            //Track Definition
            /*if(part.isFinal()){

        		if(std::abs(part.eta())>0.9 || part.pT()<0.15) continue;

        		if(pythia8->Pythia8()->event[ip].isAncestor(Ipsb[0]) || pythia8->Pythia8()->event[ip].isAncestor(Ipsb[1]) || pythia8->Pythia8()->event[ip].isAncestor(Ipsb[2])){
        			std::cout<<"this particle is from b quark"<<std::endl; 
	        	    bPartons.push_back(fastjet::PseudoJet(part.px(), part.py(), part.pz(), part.e())); 
		        }

        		if(pythia8->Pythia8()->event[ip].isAncestor(Ipsc[0]) || pythia8->Pythia8()->event[ip].isAncestor(Ipsc[1]) || pythia8->Pythia8()->event[ip].isAncestor(Ipsc[2])){
			        std::cout<<"this particle is from c quark"<<std::endl; 
	              	cPartons.push_back(fastjet::PseudoJet(part.px(), part.py(), part.pz(), part.e())); 
		        }
		
            }*/
        }

        for (Int_t ip = 0; ip < np; ip++) {
            TParticle *part = (TParticle *)particles->At(ip);
            Int_t ist = part->GetStatusCode();

            // Positive codes are final particles.
            if (ist <= 0)
                continue;

            Int_t pdg = part->GetPdgCode();
            Float_t charge = TDatabasePDG::Instance()->GetParticle(pdg)->Charge();

            if (chargedOnly) {
                if (charge == 0.)
                    continue; //charged particles only
            } else {
                if (part->GetPdgCode() == 12 || part->GetPdgCode() == 14 || part->GetPdgCode() == 16) // reject neutrinos
                    continue;
            }

            Float_t eta = part->Eta();
            Float_t pt = part->Pt();
            Float_t energy = part->Energy();

            //if (abs(eta) > 0.9)
            if (std::abs(eta) > kMaxEta)
                continue;
            if(charge == 0) {
                // ptcut on neutral particles
                if (pt < ptcutNeutral)
                    continue;
                if (energy < ecutNeutral)
                    continue;
            } else {
                // ptcut on charged particles
                if (pt < ptcutCharged)
                   continue;
                if (energy < ecutCharged)
                    continue;
            }

            input_particles.push_back(fastjet::PseudoJet(part->Px(), part->Py(), part->Pz(), part->Energy()));
        }

        if (input_particles.size() == 0) {
            //printf("No particle....\n");
            continue;
        }

        for (Int_t iR = 0; iR < nR; iR++) {

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
            if (fDoPerpCone) {
                Double_t PerpConePhi = inclusive_jets[0].phi() + TMath::Pi() / 2;
                PerpConePhi = (PerpConePhi > 2 * TMath::Pi()) ? PerpConePhi - 2 * TMath::Pi() : PerpConePhi; // fit to 0 < phi < 2pi

                Double_t PerpConeEta = inclusive_jets[0].eta();
                Double_t PerpConePt(0);

                for (unsigned int j = 0; j < input_particles.size(); j++) {

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
            } else {
                // Rho Sparse for underlying Event Subtraction
                static Double_t rhovec[999];
                Int_t NjetAcc = 0;
                Double_t TotaljetAreaPhys = 0;
                Double_t TotalTPCArea = 2 * TMath::Pi() * 0.9;

                // push all jets within selected acceptance into stack
                for (unsigned int iJets = 0; iJets < inclusive_jetsBkg.size(); ++iJets) {

                    // exlcuding leading background jets (could be signal)
                    if (iJets == 0 || iJets == 1)
                        continue;

                    if (TMath::Abs(inclusive_jetsBkg[iJets].eta()) > (0.5))
                        continue;

                    // Search for overlap with signal jets
                    Bool_t isOverlapping = kFALSE;
                    if (inclusive_jets.size() > 0) {
                        for (unsigned int j = 0; j < inclusive_jets.size(); j++) {
                            if (inclusive_jets[j].perp() < 5)
                                continue;

                            if (IsJetOverlapping(inclusive_jets[j], inclusive_jetsBkg[iJets])) {
                                isOverlapping = kTRUE;
                                break;
                            }
                        }
                    }
                    if (isOverlapping)
                        continue;

                    //This is to exclude pure ghost jets from the rho calculation
                    std::vector<fastjet::PseudoJet> ContJet = inclusive_jetsBkg[iJets].constituents();
                    if (ContJet.size() > 0) {
                        TotaljetAreaPhys += inclusive_jetsBkg[iJets].area();
                        rhovec[NjetAcc] = inclusive_jetsBkg[iJets].perp() / inclusive_jetsBkg[iJets].area();
                        ++NjetAcc;
                    }
                }

                Double_t OccCorr = TotaljetAreaPhys / TotalTPCArea;

                Double_t rho = 0.;

                if (NjetAcc > 0) {
                    //find median value
                    rho = TMath::Median(NjetAcc, rhovec);
                    rho = rho * OccCorr;
                }
                Rho = rho;
            }

            for (unsigned int i = 0; i < inclusive_jets.size(); i++) {

                if (TMath::Abs(inclusive_jets[i].eta()) > (Etavals[iR] / 2))
                    continue;

                Double_t PtSub = inclusive_jets[i].perp() - (Rho * inclusive_jets[i].area());

                hJetPtSpecJet[iR]->Fill(inclusive_jets[i].perp(), evt_wght);
                hJetPtSpecSub[iR]->Fill(PtSub, evt_wght);

                //b-jet
                for (unsigned int bjet = 0; bjet < bPartons.size(); bjet++) {
                    Double_t DeltaR = DistanceBetweenJets(inclusive_jets[i], bPartons[bjet]);
                    // std::cout<<"The distance for R="<<Rvals[iR]<<" is :"<<DeltaR<<" And the jet Eta is:"<<inclusive_jets[i].eta()<<" and the Phi is :"<<inclusive_jets[i].phi()<<std::endl;
                    if (DeltaR < (Rvals[iR])) {
                        hBJetPtSpecJet[iR]->Fill(inclusive_jets[i].perp(), evt_wght);
                        hBJetPtSpecSub[iR]->Fill(PtSub, evt_wght);
                        //std::cout<<"This is a b-jet "<std::<endl;
                        break;
                    }
                }

                //c-jet
                for (unsigned int cjet = 0; cjet < cPartons.size(); cjet++) {
                    Double_t DeltaR = DistanceBetweenJets(inclusive_jets[i], cPartons[cjet]);
                    //std::cout<<"The distance for R="<<Rvals[iR]<<" is :"<<DeltaR<<" And the jet Eta is:"<<inclusive_jets[i].eta()<<" and the Phi is :"<<inclusive_jets[i].phi()<<std::endl;
                    if (DeltaR < (Rvals[iR])) {
                        hCJetPtSpecJet[iR]->Fill(inclusive_jets[i].perp(), evt_wght);
                        hCJetPtSpecSub[iR]->Fill(PtSub, evt_wght);
                        //std::cout<<"This is a c-jet "<<std::endl;
                        break;
                    }
                }
            }
        }
        iev++;
    }

    engine.stat();

    Double_t sumw = engine.info.weightSum();
    //sumw *= 1e-9;
    Double_t TotalXSec = engine.info.sigmaGen();

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
Double_t DistanceBetweenJets(fastjet::PseudoJet jet1, fastjet::PseudoJet jet2) {

    Double_t DeltaEta = TMath::Abs(jet1.eta() - jet2.eta());
    Double_t DeltaPhi = TVector2::Phi_mpi_pi((jet1.phi() - jet2.phi()));

    Double_t DeltaR = TMath::Sqrt(DeltaPhi * DeltaPhi + DeltaEta * DeltaEta);

    return DeltaR;
}
//________________________________________________________________________
Bool_t IsBMeson(Int_t pc) {
    int bPdG[] = {511, 521, 10511, 10521, 513, 523, 10513, 10523, 20513, 20523, 20513, 20523, 515, 525, 531,
                  10531, 533, 10533, 20533, 535, 541, 10541, 543, 10543, 20543, 545, 551, 10551, 100551,
                  110551, 200551, 210551, 553, 10553, 20553, 30553, 100553, 110553, 120553, 130553, 200553, 210553, 220553,
                  300553, 9000533, 9010553, 555, 10555, 20555, 100555, 110555, 120555, 200555, 557, 100557, 5122, 5112, 5212, 5222, 5114, 5214, 5224, 5132, 5232, 5312, 5322, 5314, 5324, 5332, 5334, 5142, 5242, 5412, 5422, 5414, 5424, 5342, 5432, 5434, 5442, 5444, 5512, 5522, 5514, 5524, 5532,
                  5534, 5542, 5544, 5554};
    for (int i = 0; i < (int)(sizeof(bPdG) / sizeof(int)); ++i)
        if (std::abs(pc) == bPdG[i])
            return true;
    return false;
}
//________________________________________________________________________
Bool_t IsDMeson(Int_t pc) {
    int bPdG[] = {411, 421, 10411, 10421, 413, 423, 10413, 10423, 20431, 20423, 415,
                  425, 431, 10431, 433, 10433, 20433, 435, 441, 10441, 100441, 443, 10443, 20443,
                  100443, 30443, 9000443, 9010443, 9020443, 445, 100445, 4122, 4222, 4212, 4112, 4224, 4214, 4114, 4232, 4132, 4322, 4312, 4324, 4314, 4332, 4334, 4412, 4422, 4414, 4424, 4432, 4434, 4444};
    for (int i = 0; i < (int)(sizeof(bPdG) / sizeof(int)); ++i)
    if (abs(pc) == bPdG[i])
       return true;
    return false;
}
//________________________________________________________________________
Bool_t IsJetOverlapping(fastjet::PseudoJet jet1, fastjet::PseudoJet jet2) {

    std::vector<fastjet::PseudoJet> ContJet1 = jet1.constituents();
    std::vector<fastjet::PseudoJet> ContJet2 = jet2.constituents();

    for (unsigned int i = 0; i < ContJet1.size(); ++i) {
        //Int_t jet1Track = jet1->TrackAt(i);
        for (unsigned int j = 0; j < ContJet2.size(); ++j) {
            //Int_t jet2Track = jet2->TrackAt(j);
            if ((ContJet1[i].perp() == ContJet2[j].perp()) && (ContJet1[i].phi() == ContJet2[j].phi()) && (ContJet1[i].eta() == ContJet2[j].eta()))
                return kTRUE;
        }
    }
    return kFALSE;
}
