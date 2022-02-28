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
    TH1 *mCentral = nullptr;
    TH1 *mLower = nullptr;
    TH1 *mUpper = nullptr;

    bool operator==(const Radius &other) const { return mR == other.mR; }
    bool operator<(const Radius &other) const { return mR < other.mR; }
    
    void evaluate() {
        double radius = static_cast<double>(mR)/10.;
        mCentral = mSpectra["cent"];
        mCentral->SetDirectory(nullptr);
        mCentral->SetNameTitle(Form("jetspectrum_cent_R%02d", mR), Form("POWHEG+PYTHIA jet spectrum for R=%.1f", radius));
        mLower = static_cast<TH1 *>(mCentral->Clone());
        mLower->SetDirectory(nullptr);
        mLower->SetNameTitle(Form("jetspectrum_low_R%02d", mR), Form("POWHEG+PYTHIA jet spectrum (low) for R=%.1f", radius));
        mLower->Reset();
        mUpper = static_cast<TH1 *>(mCentral->Clone());
        mUpper->SetDirectory(nullptr);
        mUpper->SetNameTitle(Form("jetspectrum_high_R%02d", mR), Form("POWHEG+PYTHIA jet spectrum (high) for R=%.1f", radius));
        mUpper->Reset();
        std::map<std::string, double> last;
        for(auto ib : ROOT::TSeqI(0, mCentral->GetXaxis()->GetNbins())) {
            std::set<double> points;
            for(auto &[var, spec] : mSpectra) {
                double val = spec->GetBinContent(ib+1);
                if(last.find(var) != last.end()) {
                    // simple outlier cut
                    if(last[var] > 0. && val > 5 * last[var]) {
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
};


std::set<Variation> readFile(const std::string_view inputfile) {
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
            auto spectrum = gDirectory->Get<TH1>(Form("InclusiveJetXSection_R%d", R));
            spectrum->SetDirectory(nullptr);
            spectrum->Scale(1./norm);
            spectrum->Scale(1./(2*ETA - 2*radius)); // correct for acceptance
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

void MakeUncertainty(const std::string_view inputfile) {
    auto rbins = buildRadii(readFile(inputfile));
    std::unique_ptr<TFile> writer(TFile::Open("POWHEGPYTHIA_jetspectrum_sys.root","RECREATE"));
    for(auto &bin : rbins) {
        bin.evaluate();
        bin.mCentral->Write();
        bin.mLower->Write();
        bin.mUpper->Write();
    }
}