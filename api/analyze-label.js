const Anthropic = require("@anthropic-ai/sdk");

const client = new Anthropic.default({ apiKey: process.env.ANTHROPIC_API_KEY });

// =========================================================
// 日本の食品添加物データベース
// 出典: 食品安全委員会(FSCJ)・厚生労働省・WHO/FAO JECFA・EFSA・IARC
// =========================================================
const ADDITIVE_DB = {
  // ─── 保存料 ───
  "ソルビン酸": {
    category: "保存料", risk: "low",
    adi: "0〜25 mg/kg体重/日（JECFA）",
    effects: "通常の摂取量では安全とされている。過剰摂取で消化器への軽度の刺激報告あり。",
    evidence: "食品安全委員会 2007年評価済み・JECFA ADI設定済み",
    note: "カリウム塩（ソルビン酸K）として使用されることが多い。",
    tags: ["保存料"]
  },
  "ソルビン酸K": {
    category: "保存料", risk: "low",
    adi: "0〜25 mg/kg体重/日（JECFA、ソルビン酸として）",
    effects: "カリウム過剰摂取に注意（腎機能低下者）。通常摂取量では安全。",
    evidence: "食品安全委員会 評価済み・JECFA ADI設定済み",
    note: "漬物・チーズ・かまぼこ等に広く使用。",
    tags: ["保存料"]
  },
  "安息香酸": {
    category: "保存料", risk: "medium",
    adi: "0〜5 mg/kg体重/日（JECFA）",
    effects: "ビタミンC（アスコルビン酸）と反応してベンゼン（発がん性物質）を生成する可能性がある。子どものADHD様症状との関連を示す研究がある（McCann et al., Lancet 2007）。",
    evidence: "EFSA 2016年再評価・英国食品基準庁（FSA）が着色料との組み合わせで勧告",
    note: "炭酸飲料・果汁飲料に多用。ビタミンC添加飲料では特に注意が必要。",
    tags: ["保存料"]
  },
  "安息香酸Na": {
    category: "保存料", risk: "medium",
    adi: "0〜5 mg/kg体重/日（JECFA、安息香酸として）",
    effects: "ビタミンCとのベンゼン生成反応あり。子どもの多動性との関連研究あり。",
    evidence: "EFSA・FSA・JECFA 評価済み",
    note: "炭酸飲料・ドレッシング等に使用。",
    tags: ["保存料"]
  },
  "パラオキシ安息香酸エステル": {
    category: "保存料", risk: "medium",
    adi: "0〜10 mg/kg体重/日（JECFA）",
    effects: "内分泌かく乱作用（エストロゲン様作用）が動物実験で報告されている。皮膚・化粧品に使われるパラベン類と同系統。",
    evidence: "EFSA 2004年・食品安全委員会 2009年評価。EUでは一部制限。",
    note: "醤油・果実ソース・清涼飲料水に使用。",
    tags: ["保存料", "内分泌かく乱"]
  },

  // ─── 発色剤 ───
  "亜硝酸Na": {
    category: "発色剤", risk: "high",
    adi: "0〜0.06 mg/kg体重/日（JECFA）",
    effects: "体内でアミン類と反応してニトロソアミン（IARC グループ2A発がん性物質）を生成する可能性。WHO/IARCは加工肉（亜硝酸塩使用）をグループ1（発がん性あり）に分類（2015年）。メトヘモグロビン血症のリスク（特に乳幼児）。",
    evidence: "IARC 2015年分類・WHO 勧告・食品安全委員会 2010年評価",
    note: "ハム・ベーコン・ウインナー・明太子等に使用。特に加熱調理時に生成量増加。",
    tags: ["発色剤", "IARC分類", "発がん性リスク"]
  },
  "亜硝酸ナトリウム": {
    category: "発色剤", risk: "high",
    adi: "0〜0.06 mg/kg体重/日（JECFA）",
    effects: "亜硝酸Naと同一物質。ニトロソアミン生成・発がん性リスク。乳幼児には特に危険。",
    evidence: "IARC 2015年・WHO・食品安全委員会",
    note: "加工肉・魚卵製品に使用。",
    tags: ["発色剤", "IARC分類", "発がん性リスク"]
  },
  "硝酸Na": {
    category: "発色剤", risk: "medium",
    adi: "0〜3.7 mg/kg体重/日（EFSA、硝酸塩として）",
    effects: "体内で亜硝酸塩に変換される可能性。亜硝酸塩と同様のリスク経路あり。",
    evidence: "EFSA 2017年評価・食品安全委員会 評価済み",
    note: "チーズ・ハム等に使用。",
    tags: ["発色剤"]
  },

  // ─── 酸化防止剤 ───
  "BHA": {
    category: "酸化防止剤", risk: "high",
    adi: "0〜0.5 mg/kg体重/日（JECFA）",
    effects: "IARCがグループ2B（発がん性の可能性あり）に分類。動物実験でラットの前胃に腫瘍形成。内分泌かく乱作用の懸念も報告されている。",
    evidence: "IARC モノグラフ Vol.40・食品安全委員会 2007年評価・EUで一部の食品への使用禁止",
    note: "インスタント食品・スナック菓子・油脂製品に使用。EU・カリフォルニア州では規制強化。",
    tags: ["酸化防止剤", "IARC分類", "内分泌かく乱"]
  },
  "BHT": {
    category: "酸化防止剤", risk: "medium",
    adi: "0〜0.3 mg/kg体重/日（JECFA）",
    effects: "動物実験で肝臓・肺への影響が報告されている。一部の動物実験でがん促進作用も報告。結果は混在しており結論は出ていない。",
    evidence: "JECFA 評価済み・食品安全委員会 2006年評価",
    note: "油脂・バター・スナック類・即席麺に使用。",
    tags: ["酸化防止剤"]
  },
  "エリソルビン酸": {
    category: "酸化防止剤", risk: "low",
    adi: "ADI設定なし（安全性が高いため）",
    effects: "ビタミンCの立体異性体。過剰摂取でビタミンCの吸収阻害の可能性が一部で指摘されている。",
    evidence: "食品安全委員会 評価済み・JECFA 評価済み",
    note: "果実飲料・缶詰・漬物等に広く使用。",
    tags: ["酸化防止剤"]
  },
  "エリソルビン酸Na": {
    category: "酸化防止剤", risk: "low",
    adi: "ADI設定なし",
    effects: "エリソルビン酸と同様。安全性は高い。",
    evidence: "食品安全委員会 評価済み",
    note: "加工食品に広く使用。",
    tags: ["酸化防止剤"]
  },
  "亜硫酸Na": {
    category: "漂白剤・酸化防止剤", risk: "medium",
    adi: "0〜0.7 mg/kg体重/日（JECFA、二酸化硫黄として）",
    effects: "亜硫酸塩に過敏な人（喘息患者等の推定1%）でアレルギー反応・気管支痙攣を引き起こす可能性がある。アナフィラキシーの報告あり。",
    evidence: "FDA アレルゲン表示対象物質・EFSA 評価・食品安全委員会 評価済み",
    note: "ドライフルーツ・ワイン・海老等に使用。",
    tags: ["漂白剤", "アレルギー"]
  },
  "次亜硫酸Na": {
    category: "漂白剤", risk: "medium",
    adi: "0〜0.7 mg/kg体重/日（JECFA、二酸化硫黄として）",
    effects: "亜硫酸塩に敏感な人では喘息発作の誘発リスク。ビタミンB1（チアミン）を分解する特性がある。",
    evidence: "EFSA・FDA・食品安全委員会 評価済み",
    note: "水産加工品・乾燥果実・甘納豆等に使用。",
    tags: ["漂白剤", "アレルギー"]
  },

  // ─── 着色料（タール系色素）───
  "赤色2号": {
    category: "着色料（タール系）", risk: "high",
    adi: "ADIなし（FAO/WHO）",
    effects: "動物実験で催奇形性・変異原性の報告。アメリカでは使用禁止（FDA）。",
    evidence: "FAO/WHO JECFA 評価・FDA禁止物質",
    note: "日本では使用可能だが、EU・アメリカでは禁止。",
    tags: ["着色料", "タール色素", "国際規制"]
  },
  "赤色3号": {
    category: "着色料（タール系）", risk: "high",
    adi: "0〜0.1 mg/kg体重/日（JECFA）",
    effects: "動物実験で甲状腺腫瘍との関連が報告。EUでは使用禁止。FDA 2024年に禁止発表。",
    evidence: "JECFA 評価・EU禁止・FDA 2024年禁止発表",
    note: "さくらんぼ・かまぼこ等に使用。国際的に規制が強化されている。",
    tags: ["着色料", "タール色素", "国際規制"]
  },
  "赤色40号": {
    category: "着色料（タール系）", risk: "medium",
    adi: "0〜7 mg/kg体重/日（JECFA）",
    effects: "子どもの多動性・ADHD様症状との関連研究がある（McCann et al., Lancet 2007）。EUでは警告表示義務。",
    evidence: "EFSA 2008年評価・英国FSA 勧告・EU警告ラベル義務化",
    note: "清涼飲料水・菓子・アイスクリームに使用。",
    tags: ["着色料", "タール色素", "子ども"]
  },
  "赤色102号": {
    category: "着色料（タール系）", risk: "medium",
    adi: "0〜4 mg/kg体重/日（JECFA）",
    effects: "子どもの行動への影響が懸念される合成色素群の一つ。アスピリン過敏症の人に反応を起こす可能性。",
    evidence: "EU警告ラベル義務化対象・食品安全委員会 評価済み",
    note: "漬物・菓子・魚卵等に使用。",
    tags: ["着色料", "タール色素", "アレルギー"]
  },
  "黄色4号": {
    category: "着色料（タール系）", risk: "medium",
    adi: "0〜7.5 mg/kg体重/日（JECFA）",
    effects: "アスピリン過敏症や喘息患者でアレルギー反応の報告。子どもの多動との関連研究あり。ノルウェー・フィンランドでは禁止。",
    evidence: "EFSA 評価・EU警告ラベル義務化対象・食品安全委員会 評価済み",
    note: "菓子・清涼飲料水・ゼリー等に使用。タートラジンとも呼ばれる。",
    tags: ["着色料", "タール色素", "アレルギー"]
  },
  "黄色5号": {
    category: "着色料（タール系）", risk: "medium",
    adi: "0〜2.5 mg/kg体重/日（JECFA）",
    effects: "EU警告ラベル対象の6色素の一つ。子どもの行動への影響懸念。",
    evidence: "EFSA・EU警告ラベル義務化対象",
    note: "菓子・清涼飲料水等に使用。",
    tags: ["着色料", "タール色素"]
  },
  "青色1号": {
    category: "着色料（タール系）", risk: "low",
    adi: "0〜12.5 mg/kg体重/日（JECFA）",
    effects: "通常の食品使用量では問題は少ないとされる。大量摂取の動物実験で一部腫瘍との関連報告あり。",
    evidence: "JECFA 評価・食品安全委員会 評価済み",
    note: "菓子・アイスクリームに使用。EUでは一部禁止。",
    tags: ["着色料", "タール色素"]
  },
  "カラメル色素": {
    category: "着色料（カラメル）", risk: "medium",
    adi: "クラスIII・IVはADI設定なし（懸念）",
    effects: "クラスIII・IVは製造過程で4-メチルイミダゾール（4-MeI）が生成され、IARCがグループ2B（発がん性の可能性あり）に分類。",
    evidence: "IARC グループ2B（4-MeI）・カリフォルニア州Prop.65規制・EFSA評価",
    note: "コーラ・しょうゆ・ソース・ウィスキー等に広く使用。クラスI・IIは比較的安全。",
    tags: ["着色料", "IARC分類"]
  },

  // ─── 甘味料 ───
  "アスパルテーム": {
    category: "甘味料（人工）", risk: "medium",
    adi: "0〜40 mg/kg体重/日（JECFA）",
    effects: "2023年にIARCがグループ2B（発がん性の可能性あり）に分類（ただしJECFAはADI以内は安全と結論）。フェニルケトン尿症（PKU）患者には禁忌（フェニルアラニンを含むため）。",
    evidence: "IARC 2023年7月分類・JECFA 2023年評価継続・食品安全委員会 注目",
    note: "ダイエット飲料・ガム・菓子に広く使用。PKU患者は摂取不可。",
    tags: ["甘味料", "人工甘味料", "IARC分類", "アレルギー"]
  },
  "アスパルテーム・L-フェニルアラニン化合物": {
    category: "甘味料（人工）", risk: "medium",
    adi: "0〜40 mg/kg体重/日（JECFA）",
    effects: "アスパルテームと同一。フェニルケトン尿症（PKU）患者には禁忌。IARC 2023年グループ2B分類。",
    evidence: "IARC 2023年7月・JECFA 評価",
    note: "ラベル上はこの表記でPKU警告が必要。",
    tags: ["甘味料", "人工甘味料", "IARC分類", "アレルギー"]
  },
  "アセスルファムK": {
    category: "甘味料（人工）", risk: "medium",
    adi: "0〜15 mg/kg体重/日（JECFA）",
    effects: "動物実験で白血病・リンパ腫との関連が報告されている研究あり（Soffritti, 2016）。腸内細菌叢への影響を示す研究もある。",
    evidence: "JECFA 評価済み・食品安全委員会 評価済み（現行基準内で安全）",
    note: "ダイエット飲料・菓子・ガムに使用。熱に安定。",
    tags: ["甘味料", "人工甘味料"]
  },
  "スクラロース": {
    category: "甘味料（人工）", risk: "low",
    adi: "0〜15 mg/kg体重/日（JECFA）",
    effects: "一部の研究で腸内細菌叢への影響、高温加熱でクロロプロパノール生成の懸念が報告されている（Bornemann et al., 2021）。",
    evidence: "JECFA 評価済み・食品安全委員会 評価済み",
    note: "幅広い食品に使用。砂糖の約600倍の甘さ。",
    tags: ["甘味料", "人工甘味料"]
  },
  "サッカリン": {
    category: "甘味料（人工）", risk: "low",
    adi: "0〜5 mg/kg体重/日（JECFA）",
    effects: "過去にラットの膀胱がん懸念があったが、メカニズムがラット特有と判明し現在は発がん性リストから除外。腸内細菌への影響研究がある。",
    evidence: "JECFA・EFSA 現行評価では安全・食品安全委員会 評価済み",
    note: "漬物・清涼飲料水等に使用。",
    tags: ["甘味料", "人工甘味料"]
  },
  "ステビア": {
    category: "甘味料（天然）", risk: "low",
    adi: "0〜4 mg/kg体重/日（JECFA、ステビオール配糖体として）",
    effects: "天然甘味料で安全性は高い。過剰摂取で血圧低下・血糖低下の可能性（薬との相互作用）。",
    evidence: "JECFA・EFSA 評価済み・食品安全委員会 評価済み",
    note: "砂糖の200〜300倍の甘さ。糖尿病患者も使用可能（ただし医師への相談推奨）。",
    tags: ["甘味料", "天然甘味料"]
  },
  "キシリトール": {
    category: "甘味料（糖アルコール）", risk: "low",
    adi: "ADI設定なし（安全性が高いため）",
    effects: "過剰摂取（50g以上/日）で下痢・腹痛を引き起こすことがある。犬には毒性がある。",
    evidence: "JECFA・EFSA 評価済み",
    note: "ガム・歯磨き粉等に使用。",
    tags: ["甘味料", "糖アルコール"]
  },

  // ─── 増粘剤・ゲル化剤 ───
  "カラギーナン": {
    category: "増粘剤・ゲル化剤", risk: "medium",
    adi: "ADI設定なし（JECFAは現行量で安全とするが懸念意見あり）",
    effects: "動物実験・試験管内実験で腸の炎症促進、腸管バリア機能への影響が報告されている（Bhattacharyya, 2012等）。IBD（炎症性腸疾患）患者は注意。",
    evidence: "国立がん研究所（米）が研究継続・一部の研究機関が使用制限を推奨",
    note: "牛乳・ヨーグルト・ゼリー・アイスクリームに広く使用。",
    tags: ["増粘剤", "腸への影響"]
  },
  "増粘多糖類": {
    category: "増粘剤（一括名称）", risk: "low",
    adi: "一括名称のため成分による",
    effects: "一般的に安全性が高いとされるが、カラギーナン・キサンタンガム・グアーガム等を含む総称。",
    evidence: "各成分はJECFA・食品安全委員会 評価済み",
    note: "幅広い加工食品に使用。",
    tags: ["増粘剤"]
  },

  // ─── 乳化剤 ───
  "ポリソルベート80": {
    category: "乳化剤", risk: "medium",
    adi: "0〜25 mg/kg体重/日（JECFA）",
    effects: "動物実験で腸内細菌叢への影響・低グレードの腸炎誘発が報告されている（Chassaing et al., Nature 2015）。IBD患者に懸念。",
    evidence: "Chassaing et al., Nature 2015・EFSA 再評価中",
    note: "アイスクリーム・チョコレート製品に使用。",
    tags: ["乳化剤", "腸への影響"]
  },
  "レシチン": {
    category: "乳化剤", risk: "low",
    adi: "ADI設定なし（安全性が高いため）",
    effects: "大豆・卵黄由来の天然乳化剤。大豆・卵アレルギーの人は注意。過剰摂取でTMAO産生による心血管への影響を示す研究あり。",
    evidence: "JECFA・EFSA 安全と評価・食品安全委員会 評価済み",
    note: "チョコレート・マーガリン・パン等に使用。",
    tags: ["乳化剤", "アレルギー"]
  },

  // ─── pH調整剤 ───
  "リン酸塩": {
    category: "pH調整剤・結着剤", risk: "medium",
    adi: "70 mg/kg体重/日（EFSA、リンとして）",
    effects: "食品添加物由来のリン過剰摂取が現代食では懸念されている。リン過多は腎臓への負担・血管石灰化・骨密度低下のリスク。慢性腎疾患患者には特に危険。",
    evidence: "EFSA 2015年評価・腎臓学領域での複数エビデンス・厚生労働省 注意喚起",
    note: "加工肉・ハム・ソーセージ・インスタント麺・チーズに広く使用。",
    tags: ["pH調整剤", "腎臓"]
  },
  "クエン酸": {
    category: "酸味料・pH調整剤", risk: "low",
    adi: "ADI設定なし（安全性が高いため）",
    effects: "食品に自然に含まれる有機酸と同一。過剰摂取で歯のエナメル質侵食の可能性。",
    evidence: "JECFA・EFSA・食品安全委員会 安全と評価",
    note: "清涼飲料水・菓子等に使用。",
    tags: ["酸味料"]
  },

  // ─── 調味料 ───
  "グルタミン酸Na": {
    category: "調味料（アミノ酸）", risk: "low",
    adi: "ADI設定なし（安全性が高いため）",
    effects: "「中華料理症候群」との関連は科学的に否定されている（FDA）。通常の食品摂取量では問題なし。過剰摂取で一部の人に頭痛報告あり。",
    evidence: "FDA GRAS（一般的に安全）認定・JECFA 安全と評価・食品安全委員会 評価済み",
    note: "スナック・調味料・インスタント食品に使用。",
    tags: ["調味料"]
  },
  "グリシン": {
    category: "調味料（アミノ酸）", risk: "low",
    adi: "ADI設定なし",
    effects: "アミノ酸の一種。通常量では安全性が高い。",
    evidence: "食品安全委員会 評価済み・JECFA 評価済み",
    note: "おにぎり・弁当の保存性向上に使用。",
    tags: ["調味料"]
  },

  // ─── その他 ───
  "亜硫酸塩": {
    category: "保存料・漂白剤", risk: "medium",
    adi: "0〜0.7 mg/kg体重/日（JECFA）",
    effects: "喘息患者・亜硫酸塩過敏症の人ではアレルギー反応（気管支痙攣・じん麻疹等）のリスク。ビタミンB1を破壊する。",
    evidence: "FDA アレルゲン管理対象・EFSA 評価・食品安全委員会 評価済み",
    note: "ワイン・干しブドウ・エビ等に使用。",
    tags: ["保存料", "アレルギー"]
  },
  "カラメル": {
    category: "着色料（カラメル）", risk: "medium",
    adi: "クラスによる",
    effects: "カラメル色素と同様。製法によりIARC グループ2Bの4-MeIを含む可能性がある。",
    evidence: "IARC・EFSA・カリフォルニア州Prop.65",
    note: "コーラ・ソース類等に広く使用。",
    tags: ["着色料", "IARC分類"]
  },
  "香料": {
    category: "香料（一括名称）", risk: "low",
    adi: "成分による（一括名称）",
    effects: "数百種類の化合物を含む総称。一部の合成香料でアレルギー反応の報告あり。",
    evidence: "食品安全委員会・JECFA 各成分を評価",
    note: "飲料・菓子・調味料等に広く使用。",
    tags: ["香料"]
  },
};

// ─── 別名マッピング ───
const ALIAS_MAP = {
  "亜硝酸塩": "亜硝酸Na",
  "亜硝酸ソーダ": "亜硝酸Na",
  "ブチルヒドロキシアニソール": "BHA",
  "ジブチルヒドロキシトルエン": "BHT",
  "ソルビン酸カリウム": "ソルビン酸K",
  "安息香酸ナトリウム": "安息香酸Na",
  "次亜硫酸ナトリウム": "次亜硫酸Na",
  "亜硫酸ナトリウム": "亜硫酸Na",
  "グルタミン酸ナトリウム": "グルタミン酸Na",
  "アセスルファムカリウム": "アセスルファムK",
  "ポリソルベート": "ポリソルベート80",
  "硝酸ナトリウム": "硝酸Na",
  "亜硝酸ナトリウム": "亜硝酸Na",
};

function lookupAdditive(name) {
  const trimmed = name.trim();
  if (ADDITIVE_DB[trimmed]) return { name: trimmed, ...ADDITIVE_DB[trimmed] };
  const aliased = ALIAS_MAP[trimmed];
  if (aliased && ADDITIVE_DB[aliased]) return { name: trimmed, ...ADDITIVE_DB[aliased] };
  for (const [key, val] of Object.entries(ADDITIVE_DB)) {
    if (trimmed.includes(key) || key.includes(trimmed)) {
      return { name: trimmed, ...val };
    }
  }
  return null;
}

module.exports = async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") return res.status(200).end();
  if (req.method !== "POST") return res.status(405).json({ error: "Method not allowed" });

  const { imageBase64, mediaType = "image/jpeg" } = req.body;
  if (!imageBase64) return res.status(400).json({ error: "imageBase64 is required" });

  try {
    const message = await client.messages.create({
      model: "claude-haiku-4-5-20251001",
      max_tokens: 1024,
      messages: [
        {
          role: "user",
          content: [
            {
              type: "image",
              source: { type: "base64", media_type: mediaType, data: imageBase64 },
            },
            {
              type: "text",
              text: `この画像は日本の食品・飲料のラベルです。
「原材料名」「食品添加物」「原材料」などの欄に記載されているすべての食品添加物を抽出してください。

ルール:
1. 食品添加物のみを抜き出す（食材・野菜・肉・果物などは含めない）
2. 括弧内の用途名（例：(保存料)、(甘味料)など）も含めて記録
3. 一括名称（増粘多糖類、乳化剤、香料など）もそのまま抜き出す
4. 結果はJSON配列のみで返す。説明文は不要。

出力例:
["ソルビン酸K(保存料)", "グリシン(調味料)", "亜硝酸Na(発色剤)", "カラメル色素", "アスパルテーム(甘味料)"]

食品添加物が見つからない場合: []
ラベルが読めない・画像が不鮮明な場合: ["IMAGE_UNCLEAR"]`,
            },
          ],
        },
      ],
    });

    const rawText = message.content[0].text.trim();
    let detected = [];
    try {
      const match = rawText.match(/\[[\s\S]*\]/);
      if (match) detected = JSON.parse(match[0]);
    } catch (_) {
      detected = [];
    }

    if (detected.includes("IMAGE_UNCLEAR")) {
      return res.status(200).json({ status: "unclear", additives: [] });
    }

    const results = detected.map((item) => {
      const cleanName = item.replace(/\(.*?\)/g, "").trim();
      const purposeMatch = item.match(/\(([^)]+)\)/);
      const purpose = purposeMatch ? purposeMatch[1] : null;
      const dbResult = lookupAdditive(cleanName);
      return { rawName: item, name: cleanName, purpose, dbInfo: dbResult, inDb: !!dbResult };
    });

    return res.status(200).json({ status: "ok", detectedCount: results.length, additives: results });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: "Analysis failed", detail: err.message });
  }
};
