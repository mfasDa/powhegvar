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
#include <TH1.h>
#include <TH2.h>
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
#include <fastjet/config.h>
#include <fastjet/JetDefinition.hh>
#include <fastjet/ClusterSequence.hh>
#include <fastjet/PseudoJet.hh>
#include <fastjet/contrib/SoftDrop.hh>
#if FASJET_VERSION_NUMBER >= 30302
#include <fastjet/tools/Recluster.hh>
#else
#include <fastjet/contrib/Recluster.hh>
#endif 

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
            mEngine.readString(Form("PDF:pSet = LHAPDF6:%s", mPDFset.data()));
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

struct SoftDropData {
    double Zg;
    double Rg;
};

std::vector<fastjet::PseudoJet> selectParticles(TClonesArray& inputevent) {
    std::vector<fastjet::PseudoJet> result;
    for(auto part : TRangeDynCast<TParticle>(inputevent)) {
        if(part->GetPdgCode() == 90) continue;
        auto abspdg = TMath::Abs(part->GetPdgCode());
        if (abspdg == 12 || abspdg == 14 || abspdg == 16) // reject neutrinos
            continue;
        if(std::abs(part->Eta()) > 0.7) continue;
        if(part->GetStatusCode() < 0) continue;
        result.emplace_back(part->Px(), part->Py(), part->Pz(), part->Energy());
    }

    return result;
}

SoftDropData makeSoftDrop(const std::vector<fastjet::PseudoJet> &constituents, double jetradius) {
    fastjet::JetDefinition jetdef(fastjet::antikt_algorithm, jetradius * 2, fastjet::E_scheme, fastjet::BestFJ30);
    fastjet::ClusterSequence jetfinder(constituents, jetdef);
    std::vector<fastjet::PseudoJet> outputjets = jetfinder.inclusive_jets(0);
    auto sdjet = outputjets[0];
    fastjet::contrib::SoftDrop softdropAlgorithm(0, 0.1, jetradius);
    softdropAlgorithm.set_verbose_structure(true);
    fastjet::JetAlgorithm reclusterizingAlgorithm = fastjet::cambridge_aachen_algorithm;
#if FASTJET_VERSION_NUMBER >= 30302
    fastjet::Recluster reclusterizer(reclusterizingAlgorithm, 1, fastjet::Recluster::keep_only_hardest);
#else
    fastjet::contrib::Recluster reclusterizer(reclusterizingAlgorithm, 1, true);
#endif
    softdropAlgorithm.set_reclustering(true, &reclusterizer);
    auto groomed = softdropAlgorithm(sdjet);
    auto softdropstruct = groomed.structure_of<fastjet::contrib::SoftDrop>();
    return {softdropstruct.symmetry(), softdropstruct.delta_R()};
}

std::vector<SoftDropData> makeIterativeSoftDrop(const std::vector<fastjet::PseudoJet> &constituents, double jetradius) {
  double beta = 0, fZcut = 0.1;
  std::vector<SoftDropData> result;
  fastjet::JetDefinition fJetDef(fastjet::cambridge_algorithm, 1., static_cast<fastjet::RecombinationScheme>(0), fastjet::BestFJ30);
  fastjet::ClusterSequence recluster(constituents, fJetDef);
  auto outputJets = recluster.inclusive_jets(0);
  fastjet::PseudoJet harder, softer, splitting = outputJets[0];

  int drop_count = 0;
  while (splitting.has_parents(harder, softer)) {
    if (harder.perp() < softer.perp())
      std::swap(harder, softer);
    drop_count += 1;
    auto sym = softer.perp() / (harder.perp() + softer.perp()),
         geoterm = beta > 0 ? std::pow(harder.delta_R(softer) / jetradius, beta) : 1.,
         zcut = fZcut * geoterm;
    if (sym > zcut) {
      // accept splitting
      double mu2 = TMath::Abs(splitting.m2()) < 1e-5 ? 100000. : std::max(harder.m2(), softer.m2()) / splitting.m2();
      result.push_back({sym, harder.delta_R(softer)});
    }
    splitting = harder;
  }
  return result;
}

std::vector<double> getLinearBinning(double min, double max, double stepsize){
  std::vector<double> binning;
  for (auto b = min; b <= max; b += stepsize)
    binning.emplace_back(b);
  return binning;
}

void RunPythiaSoftDrop(const char *inputfile = "pwgevents.lhe", const char *foutname = "Pythia8SoftDrop.root", Int_t ndeb = 1) {
    const double MBtoPB = 1e-9;
    const double kMaxEta = 0.7;

    PythiaHandler pythia;
    TDatime dt;
    static UInt_t sseed = dt.Get();
    if (gSystem->Getenv("CONFIG_SEED")) {
        sseed = atoi(gSystem->Getenv("CONFIG_SEED"));
        std::cout << "\nseed for Random number generation is : " << sseed << std::endl;
    }    
    if(gSystem->Getenv("CONFIG_PDFSET")) {
        std::string pdfset = gSystem->Getenv("CONFIG_PDFSET");
        std::cout << "Setting pdfset: " << pdfset;
        pythia.setPDFset(pdfset.data());    
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
    pythia.configure(inputfile, sseed);
    TClonesArray particles("TParticle", 1000);
    pythia.setOutput(&particles);
    // Initialize
    pythia.init();
    auto &engine = pythia.getEngine();

    TH1F *hNEvent = new TH1F("hNEvent", "number of events; N", 1, 0, 1);
    hNEvent->SetDirectory(nullptr);
    std::vector<double> zgbinning = {0., 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5},
                        nsdbinning = getLinearBinning(-1.5, 20.5, 1.);
    std::map<int, TH2 *> hZg, hRg, hNsd;
    for(auto R = 2; R < 7; R++) {
        std::vector<double> rgbinning = {-0.05};
        double ir = 0.;
        while(ir <= double(R)/10 + 0.05) {
            rgbinning.push_back(ir);
            ir += 0.05;
        }
        auto zghist = new TH2D(Form("hZgR%02d", R), Form("Zg for R = %.1f", double(R)/10), zgbinning.size() - 1, zgbinning.data(), 500, 0., 500.);
        zghist->SetDirectory(nullptr);
        zghist->Sumw2();
        hZg[R] = zghist;
        auto rghist = new TH2D(Form("hRgR%02d", R), Form("Rg for R = %.1f", double(R)/10), rgbinning.size() - 1, rgbinning.data(), 500, 0., 500.);
        rghist->SetDirectory(nullptr);
        rghist->Sumw2();
        hRg[R] = rghist;
        auto nsdhist = new TH2D(Form("hNsdR%02d", R), Form("Nsd for R = %.1f", double(R)/10), nsdbinning.size() - 1, nsdbinning.data(), 500, 0., 500.);
        nsdhist->SetDirectory(nullptr);
        nsdhist->Sumw2();
        hNsd[R] = nsdhist;
    }

    clock_t begin_time = clock();
    int iev = 0 ;
    Double_t SumW(0);
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

        auto particlesForJetfinding = selectParticles(particles);
        for(int R = 2; R < 7; R++) {
            double jetradius = double(R) / 10.;
            fastjet::ClusterSequence jetfinder(particlesForJetfinding, fastjet::JetDefinition(fastjet::antikt_algorithm, jetradius));
            auto jets = fastjet::sorted_by_pt(jetfinder.inclusive_jets());
            for(auto jet : jets) {
                if(std::abs(jet.eta()) > 0.7 - jetradius) continue;     // restriction to EMCAL fiducial acceptance
                auto softdropresults = makeSoftDrop(jet.constituents(), jetradius);
                auto splittings = makeIterativeSoftDrop(jet.constituents(), jetradius);
                hZg[R]->Fill(softdropresults.Zg, jet.pt(), evt_wght);
                hRg[R]->Fill(softdropresults.Zg < 0.1 ? -0.01 : softdropresults.Rg, jet.pt(), evt_wght); 
                hNsd[R]->Fill(softdropresults.Zg < 0.1 ? -1. : splittings.size(), jet.pt(), evt_wght); 
            }
        }
        iev++;
    }

    Double_t sumw = engine.info.weightSum();
    //sumw *= 1e-9;
    Double_t TotalXSec = engine.info.sigmaGen();

    std::cout << "\nTotal Xsec is : " << TotalXSec << "  Total Weight is : " << sumw << "          " << SumW << std::endl;

    TProfile *crosssection = new TProfile("CrossSection", "Total cross section", 1, 0, 1);
    crosssection->SetDirectory(nullptr);
    crosssection->Fill(0.5, TotalXSec);

    TH1D *numberoftrials = new TH1D("NumberofTrials", "Number of Trials", 1, 0, 1);
    numberoftrials->SetDirectory(nullptr);
    numberoftrials->SetBinContent(1, sumw);

    std::unique_ptr<TFile> writer(TFile::Open(foutname, "RECREATE"));
    writer->cd();
    hNEvent->Write();
    crosssection->Write();
    numberoftrials->Write();
    for(auto R = 2; R < 7; R++) {
        std::string rstring = Form("R%02d", R);
        writer->mkdir(rstring.data());
        writer->cd(rstring.data());
        hZg[R]->Write();
        hRg[R]->Write();
        hNsd[R]->Write();
    }
}