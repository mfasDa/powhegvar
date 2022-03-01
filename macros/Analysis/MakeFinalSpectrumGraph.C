#ifndef __CLING__
#include <map>
#include <memory> 
#include <set>
#include <string>
#include <string_view>

#include <TCanvas.h>
#include <TFile.h>
#include <TGraphAsymmErrors.h>
#include <TH1.h>
#include <TKey.h>
#include <TPaveText.h>
#include <ROOT/TSeq.hxx>
#endif

struct Rbin{
    int mR;
    TH1 *mCentral;
    TH1 *mLower;
    TH1 *mUpper;

    bool operator==(const Rbin &other) const { return mR == other.mR; }
    bool operator<(const Rbin &other) const { return mR == other.mR; }

    TGraphAsymmErrors *build() const {
        TGraphAsymmErrors *result = new TGraphAsymmErrors;
        result->SetName(Form("jetspectrumfulljets_R%02d", mR));
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

std::vector<Rbin> readFile(const std::string_view filename, const std::vector<double> binning) {
    std::vector<Rbin> result;
    std::unique_ptr<TFile> reader(TFile::Open(filename.data(), "READ"));
    for(auto R : ROOT::TSeqI(2, 7)) {
        Rbin nextbin;
        nextbin.mR = R;
        auto centraltmp = reader->Get<TH1>(Form("jetspectrum_cent_R%02d", R)),
             lowertmp = reader->Get<TH1>(Form("jetspectrum_low_R%02d", R)),
             uppertmp = reader->Get<TH1>(Form("jetspectrum_high_R%02d", R));
        nextbin.mCentral = centraltmp->Rebin(binning.size() - 1, Form("jetspectrumRebinned_cent_R%02d", R), binning.data());
        nextbin.mLower = lowertmp->Rebin(binning.size() - 1, Form("jetspectrumRebinned_low_R%02d", R), binning.data());
        nextbin.mUpper = uppertmp->Rebin(binning.size() - 1, Form("jetspectrumRebinned_high_R%02d", R), binning.data());
        nextbin.mCentral->SetDirectory(nullptr);
        nextbin.mLower->SetDirectory(nullptr);
        nextbin.mUpper->SetDirectory(nullptr);
        nextbin.mCentral->Scale(1., "width");
        nextbin.mLower->Scale(1., "width");
        nextbin.mUpper->Scale(1., "width");
        result.push_back(nextbin);
    }
    std::sort(result.begin(), result.end(), std::less<Rbin>());
    return result;
}

void MakeFinalSpectrumGraph(const std::string_view inputfile = "POWHEGPYTHIA_jetspectrum_sys.root") {
    const std::vector<double> ptbinning = {0., 5., 10., 15., 20., 25., 30., 40., 50., 60., 70., 80., 90., 100., 110., 120., 130., 140., 160., 180., 200., 240., 280., 320.};
    auto data = readFile(inputfile, ptbinning);
    std::unique_ptr<TFile> writer(TFile::Open("POWHEGPYTHIA_13TeV_fulljets_withsys.root", "RECREATE"));
    for(auto &rb : data) {
        auto spec = rb.build();
        spec->Write(spec->GetName());
    }
}