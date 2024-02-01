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
#include <TH2F.h>
#include <TProfile.h>
#include <TClonesArray.h>
#include <TParticle.h>
#include <TDatabasePDG.h>
#include <TCanvas.h>
#include <TFile.h>
#endif

class PythiaHandler {
public:
    PythiaHandler() : mEngine(), mPDFset("default"), mTune(21), mWithMPI(false), mOutput(nullptr){}
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

        // switch off decays
        mEngine.readString("111:mayDecay  = off");
        mEngine.readString("310:mayDecay  = off");
        mEngine.readString("3122:mayDecay = off");
        mEngine.readString("3112:mayDecay = off");
        mEngine.readString("3212:mayDecay = off");
        mEngine.readString("3222:mayDecay = off");
        mEngine.readString("3312:mayDecay = off");
        mEngine.readString("3322:mayDecay = off");
        mEngine.readString("3334:mayDecay = off");

        // POWHEG Merging Parameters
        mEngine.readString("POWHEG:veto = 1");
        mEngine.readString("POWHEG:vetoCount = 1000000");
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
                                                    mEngine.event[i].isFinal() ? 1 : -1.,
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
    std::shared_ptr<Pythia8::PowhegHooks> mPowhegHooks;
    TClonesArray *mOutput;
};  

void RunPythia8Pi0s(const char *inputfile = "pwgevents.lhe", const char *foutname = "Pythia8JetSpectra.root", Int_t ndeb = 1) {
    clock_t begin_time = clock();

    const double MBtoPB = 1e-9;
    const double kMaxEta = 0.7;

    TDatime dt;
    static UInt_t sseed = dt.Get();

    if (gSystem->Getenv("CONFIG_SEED")) {
        sseed = atoi(gSystem->Getenv("CONFIG_SEED"));
        std::cout << "\nseed for Random number generation is : " << sseed << std::endl;
    }

    std::unique_ptr<TFile> fout(TFile::Open(foutname, "RECREATE"));
    TH1F *hNEvent = new TH1F("hNEvent", "number of events; N", 1, 0, 1);

    TH1 *hspectrumPi0 = new TH1F("hSpectrumPi0", "Neutral pion spectrum", 2000, 0., 200.);
    hspectrumPi0->SetDirectory(nullptr);
    TH1 *hSpectrumPiCharged = new TH1F("hSpectrumPiCharged", "charged pion spectrum", 2000, 0., 200.);
    hSpectrumPiCharged->SetDirectory(nullptr);
    TH2 *hEtaPhiPi0 = new TH2F("hEtaPhiPi0", "Eta-phi of neutral pions", 100, -0.8, 0.8, 100, 0., TMath::TwoPi());
    hEtaPhiPi0->SetDirectory(nullptr);
    TH2 *hEtaPhiPiCharged = new TH2F("hEtaPhiPiCharged", "Eta-phi of charged pions", 100, -0.8, 0.8, 100, 0., TMath::TwoPi());
    hEtaPhiPiCharged->SetDirectory(nullptr);

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

    pythia.configure(inputfile, sseed);
    pythia.setOutput(particles);
    auto &engine = pythia.getEngine();

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


        if(!pythia.generate()) {
            std::cout << "No more events ..." << std::endl;
            break;
        }   
        pythia.importParticles("All");

        Double_t evt_wght = engine.info.weight(); //Event Weight for weighted events
        evt_wght *= MBtoPB;                       // Weight is pb so *1e-9 to transform to mb

        SumW += evt_wght;

        hNEvent->Fill(0.5);

        Int_t np = particles->GetEntriesFast();

        for (Int_t ip = 0; ip < np; ip++) {
            TParticle *part = (TParticle *)particles->At(ip);
            if(TMath::Abs(part->Eta()) > 0.8) {
                continue;
            }
            if(TMath::Abs(part->GetPdgCode()) == 111) {
                hspectrumPi0->Fill(part->Pt());
                hEtaPhiPi0->Fill(part->Eta(), part->Phi());
            }
            if(TMath::Abs(part->GetPdgCode()) == 211) {
                hSpectrumPiCharged->Fill(part->Pt());
                hEtaPhiPiCharged->Fill(part->Eta(), part->Phi());
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

    hspectrumPi0->Write();
    hSpectrumPiCharged->Write();
    hEtaPhiPi0->Write();
    hEtaPhiPiCharged->Write();

    fout->Write();
} //
