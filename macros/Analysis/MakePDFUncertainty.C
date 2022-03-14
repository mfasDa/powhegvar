#ifndef __CLING__
#include <iostream>
#include <cmath>
#include <map>
#include <memory>
#include <set>
#include <string>
#include <string_view>
#include <vector>

#include <TFile.h>
#include <TH1.h>
#include <TKey.h>

#include <ROOT/TSeq.hxx>
#endif

class Variation {
    std::map<int, TH1 *> hJetSpectra;

public:
    Variation() = default;
    ~Variation() = default;

    void AddJetSpectrum(int R, TH1 *spectrum) { hJetSpectra[R] = spectrum; }
    TH1 *getSpectrumForR(int R) {
        auto found = hJetSpectra.find(R);
        if(found != hJetSpectra.end()) {
            return found->second;
        }
        return nullptr;
    }
};

class PtBin {
public:
    PtBin(double ptmin, double ptmax): fPtMin(ptmin), fPtMax(ptmax), fCentral(0.) {}
    ~PtBin() = default;

    bool operator==(const PtBin &other) const { return TMath::Abs(fPtMin - other.fPtMin) < DBL_EPSILON && TMath::Abs(fPtMax - other.fPtMax) < DBL_EPSILON; }
    bool operator<(const PtBin &other) const { return fPtMax <= other.fPtMin; }

    void setCentral(double val) { fCentral = val; }
    void addVariation(double val) { fVariations.push_back(val); }
    double getPtMin() const { return fPtMin; } 
    double getPtMax() const { return fPtMax; } 
    double getX() const { return (fPtMax + fPtMin)/2.; }
    double getEX() const {return (fPtMax - fPtMin)/2.; }
    double getY() const { return fCentral; }
    double getEY() const {
        double sum = 0;
        int nvar = 0;
        for(auto var : fVariations) {
            double diff = var - fCentral;
            sum += diff*diff;
            nvar++;
        }
        return std::sqrt(sum/(double(nvar - 1)));
    }

private:
    double fPtMin;
    double fPtMax;
    double fCentral;
    std::vector<double> fVariations;
};

TH1 *evaluate(std::map<int, Variation> data, int R) {
    std::set<PtBin> ptbins;
    auto ref = data.find(13100)->second.getSpectrumForR(R);   
    TH1 *result = static_cast<TH1 *>(ref->Clone(Form("SpectrumWithError_R%02d", R)));
    result->Reset();
    result->SetDirectory(nullptr);
    for(auto ib : ROOT::TSeqI(0, ref->GetXaxis()->GetNbins())) {
        int binID = ib+1;
        PtBin nextbin(ref->GetXaxis()->GetBinLowEdge(binID), ref->GetXaxis()->GetBinUpEdge(binID));
        for(auto &var : data) {
            double val = var.second.getSpectrumForR(R)->GetBinContent(binID);
            if(var.first == 13100) nextbin.setCentral(val);
            else nextbin.addVariation(val);
        }
        result->SetBinContent(binID, nextbin.getY());
        result->SetBinError(binID, nextbin.getEY());
    }
    return result;
}

std::map<int, Variation> readFile(const char *filename, const std::vector<double> &binning) {
    const double ETA = 0.7;
    std::unique_ptr<TFile> reader(TFile::Open(filename, "READ"));
    auto norm = reader->Get<TH1>("hNEvent")->GetBinContent(1);
    std::map<int, Variation> result;
    for(auto key : TRangeDynCast<TKey>(reader->GetListOfKeys())) {
        std::string_view keyname(key->GetName());
        if(keyname.find("pdf") != 0) continue;
        int pdfid = std::stoi(keyname.substr(3).data());
        Variation nextvar;
        reader->cd(keyname.data());
        for(auto R : ROOT::TSeqI(2, 7)) {
            double radius = double(R)/10.;
            auto inputspec = gDirectory->Get<TH1>(Form("InclusiveJetXSection_R%02d", R));
            auto spec = inputspec->Rebin(binning.size()-1, Form("%s_rebinned", inputspec->GetName()), binning.data());
            spec->SetDirectory(nullptr);
            spec->Scale(1./norm);
            spec->Scale(1., "width");
            spec->Scale(1./(2*ETA - 2*radius)); // correct for acceptance
            nextvar.AddJetSpectrum(R, spec);
        }
        result[pdfid] = nextvar;
    }
    return result;
}

TH1 *makeRelError(TH1 *spectrum, const char *source, int R) {
    auto result = static_cast<TH1 *>(spectrum->Clone(Form("relError_%s_%02d", source, R)));
    result->SetDirectory(nullptr);
    result->Reset();
    for(auto ib : ROOT::TSeqI(0, spectrum->GetXaxis()->GetNbins())) {
        double value = spectrum->GetBinContent(ib+1),
               error = spectrum->GetBinError(ib+1);
        result->SetBinContent(ib+1, error/value);
        result->SetBinError(ib+1, 0);
    }
    return result;
}

TH1 *makeCombinedPDFUncertainty(TH1 *pdf, TH1 *alphas, int R){
    auto result = static_cast<TH1 *>(pdf->Clone(Form("SpectrumWithCombinedErrors_R%02d", R)));
    result->SetDirectory(nullptr);
    result->Reset();
    for(auto ib : ROOT::TSeqI(0, pdf->GetXaxis()->GetNbins())) {
        double errpdf = pdf->GetBinError(ib+1),
               erralphas = alphas->GetBinError(ib+1);
        double errcombined = std::sqrt(errpdf*errpdf + erralphas*erralphas);
        result->SetBinContent(ib+1, pdf->GetBinContent(ib+1));
        result->SetBinError(ib+1, errcombined);
    }
    return result;
}

void MakePDFUncertainty(){
    const std::vector<double> ptbinning = {0., 5., 10., 15., 20., 25., 30., 40., 50., 60., 70., 80., 90., 100., 110., 120., 130., 140., 160., 180., 200., 240., 280., 320.};
    auto dataPDF = readFile("pdf/Pythia8JetSpectra_merged.root", ptbinning),
         dataAlphas = readFile("alphas/Pythia8JetSpectra_merged.root", ptbinning);

    std::map<int, TH1 *>combinederrors, relErrorPDF, relErrorAlphaS;
    for(auto R : ROOT::TSeqI(2, 7)) {
        auto pdferr = evaluate(dataPDF, R),
             alphaserr = evaluate(dataAlphas, R);
        combinederrors[R] = makeCombinedPDFUncertainty(pdferr, alphaserr, R);
        relErrorPDF[R] = makeRelError(pdferr, "pdf", R);
        relErrorAlphaS[R] = makeRelError(alphaserr, "alphas", R);
    }

    std::unique_ptr<TFile> output(TFile::Open("POWHEGPYTHIA_jetspectrum_syspdf.root", "RECREATE"));
    output->cd();
    for(auto R : ROOT::TSeqI(2, 7)) {
        combinederrors.find(R)->second->Write();
        relErrorPDF.find(R)->second->Write();
        relErrorAlphaS.find(R)->second->Write();
    };
}