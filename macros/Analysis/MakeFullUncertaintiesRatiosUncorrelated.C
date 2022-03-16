#ifndef __CLING__
#include <map>
#include <memory> 
#include <set>
#include <string>
#include <string_view>

#include <TCanvas.h>
#include <TGraphAsymmErrors.h>
#include <TFile.h>
#include <TH1.h>
#include <TKey.h>
#include <TLegend.h>
#include <TPaveText.h>
#include <ROOT/TSeq.hxx>
#endif

struct ratiokey {
    int numerator;
    int denominator;

    bool operator==(const ratiokey &other) const { return numerator == other.numerator && denominator == other.denominator; }
    bool operator<(const ratiokey &other) const { if(numerator == other.numerator) return denominator < other.denominator; return numerator < other.numerator; }
};

TGraphAsymmErrors *makeRatioUncorrelated(TH1 *numerator, TH1 *denominator) {
    TGraphAsymmErrors *result = new TGraphAsymmErrors;
    int np = 0;
    for(int ib : ROOT::TSeqI(0, numerator->GetXaxis()->GetNbins())) {
        double x = numerator->GetXaxis()->GetBinCenter(ib+1),
               ex = numerator->GetXaxis()->GetBinWidth(ib+1) / 2.,
               num = numerator->GetBinContent(ib+1),
               errnum = numerator->GetBinError(ib+1),
               den = denominator->GetBinContent(ib+1),
               errden = denominator->GetBinError(ib+1);
        double val = num/den,
               erelnum = errnum / num,
               erelden = errden / den,
               eval = val * std::sqrt(erelnum * erelnum + erelden * erelden);
        result->SetPoint(np, x, val);
        result->SetPointError(np, ex, ex, eval, eval);
        np++;
    }
    return result;
}

TGraphAsymmErrors *makeCombinedUncertainty(TGraphAsymmErrors *errScales, TGraphAsymmErrors *errPDF) {
    TGraphAsymmErrors *combined = new TGraphAsymmErrors;
    for(auto ip : ROOT::TSeqI(0, errScales->GetN())) {
        double x = errScales->GetX()[ip],
               ex = errScales->GetEXlow()[ip],
               y = errScales->GetY()[ip],
               eylScales = errScales->GetEYlow()[ip],
               eyhScales = errScales->GetEYhigh()[ip],
               eylPDF = errPDF->GetEYlow()[ip],
               eyhPDF = errPDF->GetEYhigh()[ip],
               eylCombined = std::sqrt(eylScales*eylScales + eylPDF*eylPDF),
               eyhCombined = std::sqrt(eyhScales*eylScales + eyhPDF*eylPDF);
        combined->SetPoint(ip, x, y);
        combined->SetPointError(ip, ex, ex, eylCombined, eyhCombined);
    }
    return combined;
}

std::map<ratiokey, TGraphAsymmErrors *> read_Scales(const char *filename) {
    // scale variations considered correlated between jet R
    std::unique_ptr<TFile> reader(TFile::Open(filename, "READ"));
    int numerator = 2;
    std::map<ratiokey, TGraphAsymmErrors *> result;
    for(auto denominator : ROOT::TSeqI(3, 7)) {
        auto spectrum =  reader->Get<TGraphAsymmErrors>(Form("jetspectrumratiofulljets_R%02dR%02d", numerator, denominator));
        result[{numerator, denominator}] = spectrum;
    }
    return result;
}

std::map<ratiokey, TGraphAsymmErrors *> read_PDF(const char *filename) {
    // assume pdf uncertainties are not correlated
    std::map<ratiokey, TGraphAsymmErrors *> result;
    std::unique_ptr<TFile> reader(TFile::Open(filename, "READ"));
    int numerator = 2;
    TH1 *spectrumnumerator = reader->Get<TH1>(Form("SpectrumWithCombinedErrors_R%02d", numerator));
    for(auto denominator : ROOT::TSeqI(3, 7)){
        TH1 *spectrumdenominator = reader->Get<TH1>(Form("SpectrumWithCombinedErrors_R%02d", denominator));
        result[{numerator, denominator}] = makeRatioUncorrelated(spectrumnumerator, spectrumdenominator);
    }
    return result;
}

void MakeFullUncertaintiesRatiosUncorrelated(){
    auto ratioWithScaleErrors = read_Scales("POWHEGPYTHIA_jetspectrumratios_sys.root"),
         ratioWithPDFErrors = read_PDF("POWHEGPYTHIA_jetspectrum_syspdf.root");
    int numerator = 2;
    std::map<ratiokey, TGraphAsymmErrors *> combined;    
    for(auto denominator : ROOT::TSeqI(3, 7)) {
        ratiokey nextratio{numerator, denominator};
        auto combineduncertainty = makeCombinedUncertainty(ratioWithScaleErrors.find(nextratio)->second, ratioWithPDFErrors.find(nextratio)->second);
        combineduncertainty->SetName(Form("jetspectrumratiofulljets_combineduncertainty_R%02dR%02d", numerator, denominator));
        combined[nextratio] = combineduncertainty;
    }

    std::unique_ptr<TFile> writer(TFile::Open("POWHEGPYTHIA_13TeV_fulljets_ratios_withfullsys.root", "RECREATE"));
    for(auto denominator : ROOT::TSeqI(3, 7)) {
        auto combineduncertainty = combined.find({numerator, denominator})->second,
             scaleuncertainty = ratioWithScaleErrors.find({numerator, denominator})->second,
             pdfuncertainty = ratioWithPDFErrors.find({numerator, denominator})->second;        
        scaleuncertainty->SetName(Form("jetspectrumratiofulljets_scaleuncertainty_R%02dR%02d", numerator, denominator));
        pdfuncertainty->SetName(Form("jetspectrumratiofulljets_pdfuncertainty_R%02dR%02d", numerator, denominator));
        combineduncertainty->Write();
        scaleuncertainty->Write();
        pdfuncertainty->Write();
    }
}