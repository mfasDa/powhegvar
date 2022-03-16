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

struct ratiokey {
    int numerator;
    int denominator;

    bool operator==(const ratiokey &other) const { return numerator == other.numerator && denominator == other.denominator; }
    bool operator<(const ratiokey &other) const { if(numerator == other.numerator) return denominator < other.denominator; return numerator < other.numerator; }
};

class Variation {
    std::map<ratiokey, TH1 *> hJetSpectra;

public:
    Variation() = default;
    ~Variation() = default;

    void AddJetSpectrumRatio(int numerator, int denominator, TH1 *spectrum) { hJetSpectra[{numerator, denominator}] = spectrum; }
    TH1 *getSpectrumRatio(int numerator, int denominator) {
        auto found = hJetSpectra.find({numerator, denominator});
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

TH1 *evaluate(std::map<int, Variation> data, int numerator, int denominator) {
    std::set<PtBin> ptbins;
    auto ref = data.find(13100)->second.getSpectrumRatio(numerator, denominator);   
    TH1 *result = static_cast<TH1 *>(ref->Clone(Form("SpectrumRatioWithError_R%02dR%02d", numerator, denominator)));
    result->Reset();
    result->SetDirectory(nullptr);
    for(auto ib : ROOT::TSeqI(0, ref->GetXaxis()->GetNbins())) {
        int binID = ib+1;
        PtBin nextbin(ref->GetXaxis()->GetBinLowEdge(binID), ref->GetXaxis()->GetBinUpEdge(binID));
        for(auto &var : data) {
            double val = var.second.getSpectrumRatio(numerator, denominator)->GetBinContent(binID);
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
    int numerator = 2;
    int numradius = double(numerator)/10.;
    for(auto key : TRangeDynCast<TKey>(reader->GetListOfKeys())) {
        std::string_view keyname(key->GetName());
        if(keyname.find("pdf") != 0) continue;
        int pdfid = std::stoi(keyname.substr(3).data());
        Variation nextvar;
        reader->cd(keyname.data());
        std::unique_ptr<TH1> numspectrum(gDirectory->Get<TH1>(Form("InclusiveJetXSection_R%02d", numerator))->Rebin(binning.size()-1, Form("InclusiveJetXSection_R%02d_rebinned", numerator), binning.data()));
        numspectrum->Scale(1./norm);
        numspectrum->Scale(1., "width");
        numspectrum->Scale(1./(2*ETA - 2*numradius)); // correct for acceptance
        for(auto denominator : ROOT::TSeqI(3, 7)) {
            double denradius = double(denominator)/10.;
            std::unique_ptr<TH1> denspectrum(gDirectory->Get<TH1>(Form("InclusiveJetXSection_R%02d", denominator))->Rebin(binning.size()-1, Form("InclusiveJetXSection_R%02d_rebinned", denominator), binning.data()));
            denspectrum->Scale(1./norm);
            denspectrum->Scale(1., "width");
            denspectrum->Scale(1./(2*ETA - 2*denradius)); // correct for acceptance
            auto ratio = static_cast<TH1 *>(numspectrum->Clone(Form("jetspectrumratio_fulljets_R%02d%02d_pdf%d", numerator, denominator, pdfid)));
            ratio->SetDirectory(nullptr);
            ratio->Divide(denspectrum.get());
            nextvar.AddJetSpectrumRatio(numerator, denominator, ratio);
        }
        result[pdfid] = nextvar;
    }
    return result;
}

TH1 *makeRelError(TH1 *spectrum, const char *source, int numerator, int denominator) {
    auto result = static_cast<TH1 *>(spectrum->Clone(Form("relError_%s_R%02dR%0d", source, numerator, denominator)));
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

TH1 *makeCombinedPDFUncertainty(TH1 *pdf, TH1 *alphas, int numerator, int denominator){
    auto result = static_cast<TH1 *>(pdf->Clone(Form("SpectrumRatioWithCombinedErrors_R%02dR%02d", numerator, denominator)));
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

void MakeCorrelatedPDFUncertaintyRatios(){
    const std::vector<double> ptbinning = {0., 5., 10., 15., 20., 25., 30., 40., 50., 60., 70., 80., 90., 100., 110., 120., 130., 140., 160., 180., 200., 240., 280., 320.};
    auto dataPDF = readFile("pdf/Pythia8JetSpectra_merged.root", ptbinning),
         dataAlphas = readFile("alphas/Pythia8JetSpectra_merged.root", ptbinning);

    int numerator = 2;
    std::map<ratiokey, TH1 *>combinederrors, relErrorPDF, relErrorAlphaS;
    for(auto denominator : ROOT::TSeqI(3, 7)) {
        auto pdferr = evaluate(dataPDF, numerator, denominator),
             alphaserr = evaluate(dataAlphas, numerator, denominator);
        combinederrors[{numerator, denominator}] = makeCombinedPDFUncertainty(pdferr, alphaserr, numerator, denominator);
        relErrorPDF[{numerator, denominator}] = makeRelError(pdferr, "pdf", numerator, denominator);
        relErrorAlphaS[{numerator, denominator}] = makeRelError(alphaserr, "alphas", numerator, denominator);
    }

    std::unique_ptr<TFile> output(TFile::Open("POWHEGPYTHIA_jetspectrumratio_syspdf.root", "RECREATE"));
    output->cd();
    for(auto denominator : ROOT::TSeqI(3, 7)) {
        combinederrors.find({numerator, denominator})->second->Write();
        relErrorPDF.find({numerator, denominator})->second->Write();
        relErrorAlphaS.find({numerator, denominator})->second->Write();
    };
}