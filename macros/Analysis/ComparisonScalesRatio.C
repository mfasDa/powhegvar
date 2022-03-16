#ifndef __CLING__
#include <map>
#include <memory>
#include <set>
#include <string>
#include <string_view>
#include <vector>

#include <TCanvas.h>
#include <TFile.h>
#include <TH1.h>
#include <TKey.h>
#include <TLegend.h>
#include <TObjArray.h>
#include <TObjString.h>
#include <TPaveText.h>
#include <TString.h>
#include <TSystem.h>
#include <ROOT/TSeq.hxx>
#endif

const double textsize = 0.05;

struct ratiokey {
    int numerator;
    int denominator;

    bool operator==(const ratiokey &other) const { return numerator == other.numerator && denominator == other.denominator; };
    bool operator<(const ratiokey &other) const { return denominator < other.denominator; }
};

struct style {
    Color_t color;
    Style_t marker;

    void Apply(TH1 *hist) const {
        hist->SetMarkerColor(color);
        hist->SetLineColor(color);
        hist->SetMarkerStyle(marker);
    }
};

std::map<ratiokey, TH1 *> readFile(const char *filename, const std::vector<double> &ptbinning) {
    const double ETA=0.7;
    std::map<int, TH1 *> cache;
    std::unique_ptr<TFile> reader(TFile::Open(filename, "READ"));
    auto nevents = reader->Get<TH1>("hNEvent")->GetBinContent(1);
    int numerator = 2;
    TH1 * numspectrum;
    for(auto R : ROOT::TSeqI(2, 7)) {
        double radius = double(R)/10.;
        auto histraw = reader->Get<TH1>(Form("InclusiveJetXSection_R%d", R));
        auto histrebinned = histraw->Rebin(ptbinning.size()-1, Form("Fulljets_R%02d_rebinned", R), ptbinning.data());
        histrebinned->Scale(1., "width");
        histrebinned->Scale(1./(nevents * (2*ETA - 2*radius)));
        if(R==numerator) numspectrum = histrebinned;
        else cache[R] = histrebinned;
    }
    std::map<ratiokey, TH1 *> result;
    for(auto [R, spec] : cache) {
        auto ratio = static_cast<TH1 *>(numspectrum->Clone(Form("RatioFullJets_R%02dR%02d_rebinned", numerator, R))); 
        ratio->SetDirectory(nullptr);
        ratio->Divide(spec);
        result[{numerator, R}] = ratio;
    }
    return result;
}

std::map<ratiokey, std::map<std::string, TH1 *>> sort_radius(const std::map<std::string, std::map<ratiokey, TH1 *>> &vardata){
    std::map<ratiokey, std::map<std::string, TH1 *>> sorted;
    for(auto R : ROOT::TSeqI(3, 7)) {
        std::map<std::string, TH1 *> rdata;
        for(auto &[varname, data] : vardata) {
            auto specturmR = data.find({2, R});
            if(specturmR != data.end()) {
                rdata[varname] = specturmR->second;
            }
        }
        sorted[{2, R}] = rdata;
    }
    return sorted;
}

void DrawSpectra(const std::map<std::string, TH1 *> &variations, const std::map<std::string, std::string> &varnames, const std::map<std::string, style> &varstyles, ratiokey ratio, bool drawLegend) {
    double radiusNum = double(ratio.numerator)/10., 
           radiusDen = double(ratio.numerator)/10.;
    auto specframe = new TH1F(Form("specframeR%02dR%02d", ratio.numerator, ratio.denominator), Form("; p_{T} (GeV/c); R=%.1f/R=%.1f", radiusNum, radiusDen), 350, 0., 350.);
    specframe->SetDirectory(nullptr);
    specframe->SetStats(false);
    specframe->GetYaxis()->SetRangeUser(0., 3.);
    specframe->GetXaxis()->SetTitleSize(textsize);
    specframe->GetXaxis()->SetLabelSize(textsize);
    specframe->GetYaxis()->SetTitleSize(textsize);
    specframe->GetYaxis()->SetLabelSize(textsize);
    specframe->Draw("axis");
    TLegend *leg = nullptr;
    if(drawLegend) {
        leg = new TLegend(0.35, 0.45, 0.95, 0.95);
        leg->SetBorderSize(0);
        leg->SetFillStyle(0);
        leg->SetTextSize(textsize);
        leg->SetTextFont(42);
        leg->Draw();
    }
    for(auto &[varname, spectrum]: variations) {
        varstyles.find(varname)->second.Apply(spectrum);
        spectrum->Draw("epsame");
        if(leg) leg->AddEntry(spectrum, varnames.find(varname)->second.data(), "lep");
    }
    gPad->Update();
}

void DrawRatios(const std::map<std::string, TH1 *> &variations, const std::map<std::string, style> &varstyles, ratiokey specratio) {
    double radiusNum = double(specratio.numerator)/10., 
           radiusDen = double(specratio.numerator)/10.;
    auto ratioframe = new TH1F(Form("ratioframeR%02dR%02d", specratio.numerator, specratio.denominator), "; p_{T} (GeV/c); ratio to cent", 350, 0., 350.);
    ratioframe->SetDirectory(nullptr);
    ratioframe->SetStats(false);
    ratioframe->GetYaxis()->SetRangeUser(0.6, 1.4);
    ratioframe->GetXaxis()->SetTitleSize(textsize);
    ratioframe->GetXaxis()->SetLabelSize(textsize);
    ratioframe->GetYaxis()->SetTitleSize(textsize);
    ratioframe->GetYaxis()->SetLabelSize(textsize);
    ratioframe->Draw("axis");
     
    auto refspectrum = variations.find("cent")->second;
    for(auto &[varname, varspectrum] : variations) {
        if(varname == "cent") continue;
        auto ratio = static_cast<TH1 *>(varspectrum->Clone(Form("Ratio_%s_cent_R%02dR%02d", varname.data(), specratio.numerator, specratio.denominator)));
        ratio->SetDirectory(nullptr);
        ratio->Divide(refspectrum);
        varstyles.find(varname)->second.Apply(ratio);
        ratio->Draw("epsame");
    }
    gPad->Update();
}

void ComparisonScalesRatio(){
    const std::vector<double> ptbinning = {0., 5., 10., 15., 20., 25., 30., 40., 50., 60., 70., 80., 90., 100., 110., 120., 130., 140., 160., 180., 200., 240., 280., 320.};
    std::array<std::string, 7> varnames = {{"cent", "muf05", "mur05", "mufr05", "muf20", "mur20", "mufr20"}};
    std::array<std::string, 7> vartitles = {{"#mu_{f}=1, #mu_{r} = 1 (cent)", "#mu_{f}=0.5, #mu_{r} = 1", "#mu_{f}=1, #mu_{r} = 0.5", "#mu_{f}=0.5, #mu_{r} = 0.5", "#mu_{f}=2, #mu_{r} = 1", "#mu_{f}=1, #mu_{r} = 2", "#mu_{f}=2, #mu_{r} = 2"}};
    std::array<Color_t, 7> colors = {{kBlack, kGreen, kViolet, kRed, kOrange, kTeal, kBlue}};
    std::array<Style_t, 7> markers = {{20, 24, 25, 26, 27, 28, 29}};
    std::map<std::string, std::string> varmap;
    std::map<std::string, std::map<ratiokey, TH1 *>> vardata;
    std::map<std::string, style> stylemap;
    for(int i : ROOT::TSeqI(0, varnames.size())) {
        varmap[varnames[i]] = vartitles[i];
        vardata[varnames[i]] = readFile(Form("%s/Pythia8JetSpectra_merged.root", varnames[i].data()), ptbinning);
        stylemap[varnames[i]] = {colors[i], markers[i]};
    }
    auto data_sorted = sort_radius(vardata);

    auto plot = new TCanvas("compScalesRatio", "POWHEG scale comparsion (spectrum ratio)", 1200, 600);
    plot->Divide(4, 2);

    int icol = 0;
    for(auto &[R, dataR] : data_sorted) {
        plot->cd(icol+1);
        gPad->SetLeftMargin(0.18);
        gPad->SetRightMargin(0.05);
        gPad->SetBottomMargin(0.12);
        gPad->SetTopMargin(0.05);
        DrawSpectra(dataR, varmap, stylemap, R, icol == 0);

        plot->cd(icol+4+1);
        gPad->SetLeftMargin(0.18);
        gPad->SetRightMargin(0.05);
        gPad->SetBottomMargin(0.12);
        gPad->SetTopMargin(0.05);
        DrawRatios(dataR, stylemap, R);
        icol++;
    }
    plot->cd();
    plot->Update();
    std::vector<std::string> formats = {"eps", "pdf", "png"};
    for(auto &form : formats) plot->SaveAs(Form("%s.%s", plot->GetName(), form.data()));
}