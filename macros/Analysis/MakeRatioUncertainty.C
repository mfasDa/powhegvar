#ifndef __CLING__
#include <iostream>
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

struct Variation {
    std::string mName;
    std::map<int, TH1 *> mSpectra;

    bool operator==(const Variation &other) const { return mName == other.mName; }
    bool operator<(const Variation &other) const { return mName < other.mName; }
};

struct Radius {
    int mR;
    std::map<std::string, TH1 *> mSpectra;

    bool operator==(const Radius &other) const { return mR == other.mR; }
    bool operator<(const Radius &other) const { return mR < other.mR; }
    
};

struct Ratio {
    Radius mNumerator;
    Radius mDenominator;
    TH1 *mCentral = nullptr;
    TH1 *mLower = nullptr;
    TH1 *mUpper = nullptr;
    std::map<std::string, TH1 *> mRatiosVar; 

    void prepare() {
        for(auto &[var, spec] : mNumerator.mSpectra) {
            auto ratio = static_cast<TH1 *>(spec->Clone(Form("RatioR%02dR%02d_%s", mNumerator.mR, mDenominator.mR, var.data())));
            ratio->SetDirectory(nullptr);
            auto specDen = mDenominator.mSpectra.find(var);
            ratio->Divide(specDen->second);
            mRatiosVar[var] = ratio;
        }
    }

    void evaluate() {
        prepare();
        double radiusNum = static_cast<double>(mNumerator.mR)/10.,
               radiusDen = static_cast<double>(mDenominator.mR)/10.;
        mCentral = mRatiosVar["cent"];
        mCentral->SetDirectory(nullptr);
        mCentral->SetNameTitle(Form("jetspectrumratio_cent_R%02dR%02d", mNumerator.mR, mDenominator.mR), Form("POWHEG+PYTHIA jet spectrum for R=%.1f/R=%.1f", radiusNum, radiusDen));
        mLower = static_cast<TH1 *>(mCentral->Clone());
        mLower->SetDirectory(nullptr);
        mLower->SetNameTitle(Form("jetspectrumratio_low_R%02dR%02d", mNumerator.mR, mDenominator.mR), Form("POWHEG+PYTHIA jet spectrum (low) for R=%.1f/R=%.1f", radiusNum, radiusDen));
        mLower->Reset();
        mUpper = static_cast<TH1 *>(mCentral->Clone());
        mUpper->SetDirectory(nullptr);
        mUpper->SetNameTitle(Form("jetspectrumratio_high_R%02dR%02d", mNumerator.mR, mDenominator.mR), Form("POWHEG+PYTHIA jet spectrum (high) for  R=%.1f/R=%.1f", radiusNum, radiusDen));
        mUpper->Reset();
        std::map<std::string, double> last;
        for(auto ib : ROOT::TSeqI(0, mCentral->GetXaxis()->GetNbins())) {
            std::set<double> points;
            for(auto &[var, spec] : mRatiosVar) {
                double val = spec->GetBinContent(ib+1);
                if(last.find(var) != last.end()) {
                    // simple outlier cut
                    if(last[var] > 0. && val > 1.5 * last[var]) {
                        continue;
                    }
                }
                if(val > 0.) last[var] = val;
                points.insert(val);
            }
            // Take min and max variation for each point
            mLower->SetBinContent(ib+1, *(points.begin()));
            mUpper->SetBinContent(ib+1, *(points.rbegin()));
        }
    }

    TGraphAsymmErrors *makeUncertaintyGraph(){
        TGraphAsymmErrors *result = new TGraphAsymmErrors;
        result->SetName(Form("jetspectrumratiofulljets_R%02dR%02d", mNumerator.mR, mDenominator.mR));
        for(auto ib : ROOT::TSeqI(0, mCentral->GetXaxis()->GetNbins())) {
            double x = mCentral->GetXaxis()->GetBinCenter(ib+1),
                   y = mCentral->GetBinContent(ib+1),
                   ex = mCentral->GetXaxis()->GetBinWidth(ib+1)/2,
                   eylow = TMath::Abs(mCentral->GetBinContent(ib+1) - mLower->GetBinContent(ib+1)),
                   eyhigh = TMath::Abs(mUpper->GetBinContent(ib+1) - mCentral->GetBinContent(ib+1));
            result->SetPoint(ib, x, y);
            result->SetPointError(ib, ex, ex, eylow, eyhigh);
        }
        return result;
    }
};

std::set<Variation> readFile(const std::string_view inputfile, const std::vector<double> &binning) {
    const double ETA = 0.7;
    std::set<Variation> result;
    std::unique_ptr<TFile> reader(TFile::Open(inputfile.data(), "READ"));
    for(auto directory : TRangeDynCast<TKey>(reader->GetListOfKeys())) {
        std::string_view varname = directory->GetName();
        reader->cd(varname.data());
        Variation var;
        var.mName = varname.data();
        auto norm = gDirectory->Get<TH1>("hNEvent")->GetBinContent(1);
        for(auto R : ROOT::TSeqI(2, 7)){
            double radius = double(R)/10.;
            auto spectrumOrig = gDirectory->Get<TH1>(Form("InclusiveJetXSection_R%d", R));
            auto spectrum = spectrumOrig->Rebin(binning.size() - 1, Form("InclusiveJetXSectionRebinned_R%d", R), binning.data());
            spectrum->SetDirectory(nullptr);
            spectrum->Scale(1./norm);
            spectrum->Scale(1./(2*ETA - 2*radius)); // correct for acceptance
            spectrum->Scale(1., "width");
            var.mSpectra[R] = spectrum;
        }
        result.insert(var);
    }
    return result;
}

std::vector<Radius> buildRadii(const std::set<Variation> &variations) {
    std::vector<Radius> result;
    for(auto R : ROOT::TSeqI(2,7)){
        Radius nextR;
        nextR.mR = R;
        for(auto &var : variations) {
            auto found = var.mSpectra.find(R);
            if(found != var.mSpectra.end()){
                nextR.mSpectra[var.mName] = found->second;
            }
        }
        result.push_back(nextR);
    }
    std::sort(result.begin(), result.end(), std::less<Radius>());
    return result;
}

void MakeRatioUncertainty(const std::string_view inputfile = "POWHEGPYTHIA_sysvar.root") {
    const std::vector<double> ptbinning = {0., 5., 10., 15., 20., 25., 30., 40., 50., 60., 70., 80., 90., 100., 110., 120., 130., 140., 160., 180., 200., 240., 280., 320.};
    auto rbins = buildRadii(readFile(inputfile, ptbinning));
    std::vector<Ratio> ratios;
    Radius numerator;
    for(auto &rb : rbins) {
        if(rb.mR == 2) numerator = rb;
        else {
            Ratio next;
            next.mDenominator = rb;
            ratios.push_back(next);
        }
    }
    std::unique_ptr<TFile> writer(TFile::Open("POWHEGPYTHIA_jetspectrumratios_sys.root","RECREATE"));
    for(auto &rat : ratios) {
        rat.mNumerator = numerator;
        rat.evaluate();
        auto finalratio = rat.makeUncertaintyGraph();
        finalratio->Write(finalratio->GetName());
    }
}