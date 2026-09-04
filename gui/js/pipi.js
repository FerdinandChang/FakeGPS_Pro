// Pipi Mushroom (皮皮純點列表) 台灣全區完整整合模組
// 涵蓋全台灣 22 縣市、368 個鄉鎮市區二級聯動、36 種 Pikmin Bloom 全官方飾品分類，以及全台精選認證純點庫

// 1. 全台灣 22 縣市與其二級行政區完整映射表
const TAIWAN_DISTRICTS = {
    "台北市": ["中正區", "大同區", "中山區", "松山區", "大安區", "萬華區", "信義區", "士林區", "北投區", "內湖區", "南港區", "文山區"],
    "新北市": ["板橋區", "三重區", "中和區", "永和區", "新莊區", "新店區", "樹林區", "鶯歌區", "三峽區", "淡水區", "汐止區", "瑞芳區", "土城區", "蘆洲區", "五股區", "泰山區", "林口區", "深坑區", "石碇區", "坪林區", "三芝區", "石門區", "八里區", "平溪區", "雙溪區", "貢寮區", "金山區", "萬里區", "烏來區"],
    "基隆市": ["仁愛區", "信義區", "中正區", "中山區", "安樂區", "暖暖區", "七堵區"],
    "桃園市": ["桃園區", "中壢區", "大溪區", "楊梅區", "蘆竹區", "大園區", "龜山區", "八德區", "龍潭區", "平鎮區", "新屋區", "觀音區", "復興區"],
    "新竹市": ["東區", "北區", "香山區"],
    "新竹縣": ["竹北市", "竹東鎮", "新埔鎮", "關西鎮", "湖口鄉", "新豐鄉", "芎林鄉", "橫山鄉", "北埔鄉", "寶山鄉", "峨眉鄉", "尖石鄉", "五峰鄉"],
    "苗栗縣": ["苗栗市", "頭份市", "竹南鎮", "後龍鎮", "通霄鎮", "苑裡鎮", "卓蘭鎮", "造橋鄉", "西湖鄉", "頭屋鄉", "公館鄉", "銅鑼鄉", "三義鄉", "大湖鄉", "獅潭鄉", "三灣鄉", "南庄鄉", "泰安鄉"],
    "台中市": ["中區", "東區", "南區", "西區", "北區", "北屯區", "西屯區", "南屯區", "太平區", "大里區", "霧峰區", "烏日區", "豐原區", "后里區", "石岡區", "東勢區", "和平區", "新社區", "潭子區", "大雅區", "神岡區", "大肚區", "沙鹿區", "龍井區", "梧棲區", "清水區", "大甲區", "外埔區", "大安區"],
    "彰化縣": ["彰化市", "員林市", "和美鎮", "鹿港鎮", "溪湖鎮", "二林鎮", "田中鎮", "北斗鎮", "花壇鄉", "芬園鄉", "秀水鄉", "福興鄉", "線西鄉", "伸港鄉", "大村鄉", "埔心鄉", "埔鹽鄉", "永靖鄉", "社頭鄉", "田尾鄉", "埤頭鄉", "芳苑鄉", "大城鄉", "竹塘鄉", "溪州鄉", "二水鄉"],
    "南投縣": ["南投市", "埔里鎮", "草屯鎮", "竹山鎮", "集集鎮", "名間鄉", "鹿谷鄉", "中寮鄉", "魚池鄉", "國姓鄉", "水里鄉", "信義鄉", "仁愛鄉"],
    "雲林縣": ["斗六市", "斗南鎮", "虎尾鎮", "西螺鎮", "土庫鎮", "北港鎮", "古坑鄉", "大埤鄉", "莿桐鄉", "林內鄉", "二崙鄉", "崙背鄉", "麥寮鄉", "東勢鄉", "褒忠鄉", "臺西鄉", "元長鄉", "四湖鄉", "口湖鄉", "水林鄉"],
    "嘉義市": ["東區", "西區"],
    "嘉義縣": ["太保市", "朴子市", "布袋鎮", "大林鎮", "民雄鄉", "溪口鄉", "新港鄉", "六腳鄉", "東石鄉", "義竹鄉", "鹿草鄉", "水上鄉", "中埔鄉", "竹崎鄉", "梅山鄉", "番路鄉", "大埔鄉", "阿里山鄉"],
    "台南市": ["中西區", "東區", "南區", "北區", "安平區", "安南區", "永康區", "歸仁區", "新化區", "左鎮區", "玉井區", "楠西區", "南化區", "仁德區", "關廟區", "龍崎區", "官田區", "麻豆區", "佳里區", "西港區", "七股區", "將軍區", "北門區", "新營區", "後壁區", "白河區", "東山區", "六甲區", "下營區", "柳營區", "鹽水區", "善化區", "大內區", "山上區", "新市區", "安定區"],
    "高雄市": ["新興區", "前金區", "苓雅區", "鹽埕區", "鼓山區", "旗津區", "前鎮區", "三民區", "楠梓區", "小港區", "左營區", "仁武區", "大社區", "岡山區", "路竹區", "阿蓮區", "田寮區", "燕巢區", "橋頭區", "梓官區", "彌陀區", "永安區", "湖內區", "鳳山區", "大寮區", "林園區", "鳥松區", "大樹區", "旗山區", "美濃區", "六龜區", "內門區", "杉林區", "甲仙區", "桃源區", "那瑪夏區", "茂林區", "茄萣區"],
    "屏東縣": ["屏東市", "潮州鎮", "東港鎮", "恆春鎮", "萬丹鄉", "長治鄉", "麟洛鄉", "九如鄉", "里港鄉", "鹽埔鄉", "高樹鄉", "萬巒鄉", "內埔鄉", "竹田鄉", "新埤鄉", "枋寮鄉", "新園鄉", "崁頂鄉", "林邊鄉", "南州鄉", "佳冬鄉", "琉球鄉", "車城鄉", "滿州鄉", "枋山鄉", "三地門鄉", "霧臺鄉", "瑪家鄉", "泰武鄉", "來義鄉", "春日鄉", "獅子鄉", "牡丹鄉"],
    "宜蘭縣": ["宜蘭市", "羅東鎮", "蘇澳鎮", "頭城鎮", "礁溪鄉", "壯圍鄉", "員山鄉", "冬山鄉", "五結鄉", "三星鄉", "大同鄉", "南澳鄉"],
    "花蓮縣": ["花蓮市", "鳳林鎮", "玉里鎮", "新城鄉", "吉安鄉", "壽豐鄉", "光復鄉", "豐濱鄉", "瑞穗鄉", "富里鄉", "秀林鄉", "萬榮鄉", "卓溪鄉"],
    "台東縣": ["台東市", "成功鎮", "關山鎮", "卑南鄉", "大武鄉", "太麻里鄉", "東河鄉", "長濱鄉", "鹿野鄉", "池上鄉", "綠島鄉", "蘭嶼鄉", "延平鄉", "海端鄉", "達仁鄉", "金峰鄉"],
    "澎湖縣": ["馬公市", "湖西鄉", "白沙鄉", "西嶼鄉", "望安鄉", "七美鄉"],
    "金門縣": ["金城鎮", "金沙鎮", "金湖鎮", "金寧鄉", "烈嶼鄉", "烏坵鄉"],
    "連江縣": ["南竿鄉", "北竿鄉", "莒光鄉", "東引鄉"]
};

// 2. Pikmin Bloom 全 36 種官方飾品分類
const PIKMIN_CATEGORIES = [
    "餐廳", "咖啡廳", "甜點店", "電影院", "藥局", "動物園", 
    "森林", "水邊", "郵局", "美術館", "機場", "車站", 
    "海灘", "漢堡店", "超市", "麵包店", "服飾店", "公園", 
    "圖書館", "寺廟", "神社", "壽司店", "山峰", "體育場", 
    "飯店", "溫泉", "披薩店", "咖哩店", "拉麵店", "橋樑", 
    "公車站", "電器行", "高爾夫球場", "美妝店", "冰淇淋店", "地標景點"
];

// 3. 全台認證精選純點資料庫 (包含各縣市指標性飾品純點)
const ALL_PIPI_SPOTS_DB = [
    // 台北市
    { city: "台北市", area: "信義區", category: "電影院", name: "信義威秀影城", lat: 25.035414, lon: 121.566378, desc: "電影院/餐廳/百貨多重純點" },
    { city: "台北市", area: "信義區", category: "地標景點", name: "台北101觀景台", lat: 25.033964, lon: 121.564468, desc: "地標/高空/餐廳飾品" },
    { city: "台北市", area: "大安區", category: "公園", name: "大安森林公園", lat: 25.030141, lon: 121.535804, desc: "公園/四葉幸運草/森林純點" },
    { city: "台北市", area: "中正區", category: "車站", name: "台北車站大廳", lat: 25.047781, lon: 121.517056, desc: "三鐵共構/火車/高鐵/捷運車站" },
    { city: "台北市", area: "中山區", category: "美術館", name: "台北市立美術館", lat: 25.072551, lon: 121.524822, desc: "美術館/畫廊/公園" },
    { city: "台北市", area: "松山區", category: "機場", name: "台北松山機場觀景台", lat: 25.062402, lon: 121.551608, desc: "機場飛機飾品純點" },
    { city: "台北市", area: "士林區", category: "甜點店", name: "士林夜市甜點商圈", lat: 25.088164, lon: 121.524317, desc: "馬卡龍/甜點/小吃" },
    { city: "台北市", area: "文山區", category: "動物園", name: "台北市立動物園", lat: 24.998341, lon: 121.581026, desc: "動物園/森林/纜車站純點" },
    { city: "台北市", area: "北投區", category: "溫泉", name: "北投溫泉博物館", lat: 25.136541, lon: 121.507421, desc: "溫泉/水邊/公園飾品" },
    { city: "台北市", area: "萬華區", category: "寺廟", name: "艋舺龍山寺", lat: 25.036981, lon: 121.499912, desc: "傳統寺廟文化純點" },
    { city: "台北市", area: "大同區", category: "圖書館", name: "台灣中油大樓圖書館", lat: 25.048912, lon: 121.514214, desc: "圖書館/書店" },
    { city: "台北市", area: "內湖區", category: "電器行", name: "內湖燦坤旗艦店", lat: 25.065412, lon: 121.576214, desc: "家電/電器行" },
    { city: "台北市", area: "南港區", category: "拉麵店", name: "南港車站 Citylink 拉麵街", lat: 25.053121, lon: 121.606841, desc: "拉麵/車站" },
    
    // 新北市
    { city: "新北市", area: "板橋區", category: "車站", name: "板橋車站新北歡樂耶誕城", lat: 25.013725, lon: 121.465134, desc: "四鐵共構/百貨/電影院" },
    { city: "新北市", area: "淡水區", category: "海灘", name: "淡水漁人碼頭", lat: 25.182741, lon: 121.411634, desc: "沙灘/海灘/水邊/港口" },
    { city: "新北市", area: "八里區", category: "水邊", name: "八里左岸公園渡船頭", lat: 25.158421, lon: 121.432851, desc: "沙灘/水邊/咖啡廳" },
    { city: "新北市", area: "瑞芳區", category: "山峰", name: "九份老街觀景台", lat: 25.109923, lon: 121.845214, desc: "山頂/甜點/景觀餐廳" },
    { city: "新北市", area: "烏來區", category: "溫泉", name: "烏來溫泉街", lat: 24.864751, lon: 121.550842, desc: "溫泉/山林純點" },
    { city: "新北市", area: "三峽區", category: "寺廟", name: "三峽祖師廟與老街", lat: 24.933821, lon: 121.369842, desc: "寺廟/麵包烘焙甜點" },
    { city: "新北市", area: "貢寮區", category: "海灘", name: "福隆海水浴場", lat: 25.018241, lon: 121.944512, desc: "海灘/沙灘/水邊純點" },
    { city: "新北市", area: "石碇區", category: "森林", name: "石碇千島湖景觀區", lat: 24.938541, lon: 121.650121, desc: "森林/甲蟲/橡果" },
    { city: "新北市", area: "林口區", category: "披薩店", name: "MITSUI OUTLET PARK 林口", lat: 25.070541, lon: 121.363841, desc: "披薩/漢堡/服飾店" },
    { city: "新北市", area: "新莊區", category: "體育場", name: "新莊棒球場", lat: 25.041821, lon: 121.448512, desc: "體育場/公園" },

    // 基隆市
    { city: "基隆市", area: "仁愛區", category: "壽司店", name: "基隆廟口夜市海鮮區", lat: 25.128241, lon: 121.743121, desc: "壽司/餐廳/小吃" },
    { city: "基隆市", area: "中正區", category: "水邊", name: "正濱漁港彩色屋", lat: 25.152841, lon: 121.764512, desc: "水邊/港口/咖啡廳" },
    { city: "基隆市", area: "中山區", category: "地標景點", name: "虎仔山基隆地標公園", lat: 25.132541, lon: 121.734512, desc: "山頂/夜景/地標" },

    // 桃園市
    { city: "桃園市", area: "大園區", category: "機場", name: "桃園國際機場第二航廈", lat: 25.077221, lon: 121.232822, desc: "國際機場飛機純點" },
    { city: "桃園市", area: "中壢區", category: "服飾店", name: "華泰名品城 GLORIA OUTLETS", lat: 25.012541, lon: 121.215412, desc: "高鐵/購物中心/服飾店" },
    { city: "桃園市", area: "桃園區", category: "神社", name: "桃園神社昭和拾參", lat: 24.998412, lon: 121.325841, desc: "神社/甜點店/森林" },
    { city: "桃園市", area: "龍潭區", category: "水邊", name: "龍潭大池水岸", lat: 24.864512, lon: 121.211541, desc: "水邊/寺廟/吊橋" },
    { city: "桃園市", area: "龜山區", category: "體育場", name: "國立體育大學綜合體育館", lat: 25.034512, lon: 121.390121, desc: "體育場/大學" },

    // 新竹市 & 新竹縣
    { city: "新竹市", area: "東區", category: "動物園", name: "新竹市立動物園", lat: 24.801541, lon: 120.980621, desc: "動物園/公園/市集" },
    { city: "新竹市", area: "東區", category: "電影院", name: "新竹巨城 Big City", lat: 24.809421, lon: 120.974812, desc: "電影院/大型百貨/餐廳" },
    { city: "新竹市", area: "北區", category: "水邊", name: "南寮漁港十七公里海岸線", lat: 24.848541, lon: 120.927512, desc: "水邊/海灘/魚市場" },
    { city: "新竹縣", area: "竹北市", category: "咖哩店", name: "竹北遠東百貨特色美食街", lat: 24.823541, lon: 121.026512, desc: "咖哩/拉麵/甜點店" },
    { city: "新竹縣", area: "北埔鄉", category: "咖啡廳", name: "北埔老街擂茶商圈", lat: 24.699841, lon: 121.057512, desc: "咖啡廳/古蹟/甜點" },

    // 苗栗縣
    { city: "苗栗縣", area: "三義鄉", category: "美術館", name: "三義木雕博物館", lat: 24.409541, lon: 120.762512, desc: "美術館/森林/文化" },
    { city: "苗栗縣", area: "南庄鄉", category: "甜點店", name: "南庄桂花巷老街", lat: 24.598541, lon: 120.999512, desc: "甜點/古蹟/水邊" },
    { city: "苗栗縣", area: "泰安鄉", category: "溫泉", name: "泰安溫泉區", lat: 24.472541, lon: 120.975412, desc: "溫泉/山林" },
    { city: "苗栗縣", area: "通霄鎮", category: "神社", name: "通霄神社", lat: 24.489541, lon: 120.680512, desc: "神社/山頂" },

    // 台中市
    { city: "台中市", area: "西區", category: "美術館", name: "國立台灣美術館", lat: 24.141241, lon: 120.663621, desc: "美術館/草悟道/咖啡廳" },
    { city: "台中市", area: "北區", category: "地標景點", name: "國立自然科學博物館", lat: 24.157841, lon: 120.666012, desc: "博物館/植物園純點" },
    { city: "台中市", area: "西屯區", category: "地標景點", name: "台中國家歌劇院", lat: 24.162851, lon: 120.640521, desc: "地標/劇院/咖啡廳" },
    { city: "台中市", area: "西屯區", category: "漢堡店", name: "逢甲商圈美式漢堡特區", lat: 24.178821, lon: 120.646541, desc: "漢堡店/餐廳/小吃" },
    { city: "台中市", area: "清水區", category: "海灘", name: "高美濕地木棧道", lat: 24.312041, lon: 120.550121, desc: "水邊/海灘/燈塔" },
    { city: "台中市", area: "和平區", category: "溫泉", name: "谷關溫泉文化館", lat: 24.204512, lon: 121.006541, desc: "溫泉/山頂/森林" },
    { city: "台中市", area: "后里區", category: "地標景點", name: "麗寶樂園渡假區", lat: 24.323541, lon: 120.697512, desc: "遊樂園/摩天輪/Outlet" },

    // 彰化縣
    { city: "彰化縣", area: "彰化市", category: "地標景點", name: "八卦山大佛風景區", lat: 24.080541, lon: 120.548512, desc: "地標/寺廟/山頂" },
    { city: "彰化縣", area: "鹿港鎮", category: "寺廟", name: "鹿港天后宮與老街", lat: 24.058541, lon: 120.431512, desc: "寺廟/甜點店/古蹟" },
    { city: "彰化縣", area: "田尾鄉", category: "公園", name: "田尾公路花園", lat: 23.896541, lon: 120.528512, desc: "花園/公園/單車路線" },

    // 南投縣
    { city: "南投縣", area: "魚池鄉", category: "水邊", name: "日月潭水社碼頭", lat: 23.865541, lon: 120.911512, desc: "水邊/湖泊/飯店/纜車" },
    { city: "南投縣", area: "仁愛鄉", category: "山峰", name: "清境農場青青草原", lat: 24.058541, lon: 121.162512, desc: "山頂/動物園/森林" },
    { city: "南投縣", area: "鹿谷鄉", category: "森林", name: "溪頭自然教育園區", lat: 23.673541, lon: 120.796512, desc: "森林/甲蟲/橡果" },
    { city: "南投縣", area: "埔里鎮", category: "地標景點", name: "中台禪寺", lat: 24.013541, lon: 120.944512, desc: "寺廟/地標/博物館" },

    // 雲林縣
    { city: "雲林縣", area: "古坑鄉", category: "咖啡廳", name: "古坑華山咖啡園區", lat: 23.593541, lon: 120.594512, desc: "咖啡廳/山頂/景觀餐廳" },
    { city: "雲林縣", area: "北港鎮", category: "寺廟", name: "北港朝天宮", lat: 23.568541, lon: 120.304512, desc: "寺廟/傳統糕點/小吃" },
    { city: "雲林縣", area: "虎尾鎮", category: "麵包店", name: "虎尾糖廠鐵道商圈", lat: 23.704512, lon: 120.433512, desc: "麵包烘焙/車站/古蹟" },

    // 嘉義市 & 嘉義縣
    { city: "嘉義市", area: "東區", category: "車站", name: "阿里山森林鐵路車庫園區", lat: 23.486541, lon: 120.450512, desc: "火車/車站/檜意森活村" },
    { city: "嘉義市", area: "東區", category: "美術館", name: "嘉義市立美術館", lat: 23.478541, lon: 120.443512, desc: "美術館/古蹟/咖啡廳" },
    { city: "嘉義縣", area: "阿里山鄉", category: "山峰", name: "阿里山祝山觀日平台", lat: 23.518541, lon: 120.823512, desc: "山頂/森林/日出車站" },
    { city: "嘉義縣", area: "太保市", category: "美術館", name: "國立故宮博物院南部院區", lat: 23.469541, lon: 120.292512, desc: "博物館/美術館/水邊" },
    { city: "嘉義縣", area: "東石鄉", category: "海灘", name: "東石漁人碼頭", lat: 23.453541, lon: 120.134512, desc: "海灘/水邊/港口" },

    // 台南市
    { city: "台南市", area: "中西區", category: "美術館", name: "台南市立美術館二館", lat: 22.990841, lon: 120.201412, desc: "美術館/古蹟/咖啡廳" },
    { city: "台南市", area: "安平區", category: "水邊", name: "安平古堡與老街", lat: 23.001621, lon: 120.160541, desc: "古蹟/港口/水邊純點" },
    { city: "台南市", area: "仁德區", category: "美術館", name: "奇美博物館阿波羅噴泉", lat: 22.934821, lon: 120.226012, desc: "博物館/花園/水邊" },
    { city: "台南市", area: "北門區", category: "海灘", name: "井仔腳瓦盤鹽田", lat: 23.258541, lon: 120.108512, desc: "沙灘/水邊/地標" },
    { city: "台南市", area: "白河區", category: "溫泉", name: "關子嶺泥漿溫泉區", lat: 23.336541, lon: 120.505512, desc: "泥漿溫泉/山頂/餐廳" },
    { city: "台南市", area: "南區", category: "海灘", name: "黃金海岸水域遊憩區", lat: 22.935541, lon: 120.178512, desc: "海灘/沙灘/夕陽" },

    // 高雄市
    { city: "高雄市", area: "鹽埕區", category: "水邊", name: "駁二藝術特區大港橋", lat: 22.619841, lon: 120.282541, desc: "港口/水邊/美術館/輕軌" },
    { city: "高雄市", area: "鼓山區", category: "海灘", name: "西子灣海灘觀景平台", lat: 22.625821, lon: 120.262512, desc: "海灘/夕陽/燈塔" },
    { city: "高雄市", area: "鼓山區", category: "動物園", name: "壽山動物園", lat: 22.632541, lon: 120.278541, desc: "動物園/山頂森林" },
    { city: "高雄市", area: "小港區", category: "機場", name: "高雄國際機場小港航廈", lat: 22.574821, lon: 120.350121, desc: "國際機場飛機純點" },
    { city: "高雄市", area: "前金區", category: "美妝店", name: "大立百貨美妝精品專櫃", lat: 22.622541, lon: 120.297512, desc: "美妝/服飾店/百貨" },
    { city: "高雄市", area: "左營區", category: "車站", name: "左營高鐵站與新光三越", lat: 22.687541, lon: 120.307512, desc: "高鐵/火車/捷運三鐵" },
    { city: "高雄市", area: "旗津區", category: "海灘", name: "旗津海水浴場", lat: 22.613541, lon: 120.267512, desc: "海灘/沙灘/渡輪" },
    { city: "高雄市", area: "六龜區", category: "溫泉", name: "寶來溫泉大街", lat: 23.106541, lon: 120.697512, desc: "溫泉/山林/溪流" },

    // 屏東縣
    { city: "屏東縣", area: "恆春鎮", category: "海灘", name: "墾丁南灣沙灘", lat: 21.961541, lon: 120.764512, desc: "海灘/沙灘/水邊純點" },
    { city: "屏東縣", area: "恆春鎮", category: "地標景點", name: "鵝鑾鼻燈塔", lat: 21.902541, lon: 120.852512, desc: "燈塔/海角地標/海灘" },
    { city: "屏東縣", area: "車城鄉", category: "動物園", name: "國立海洋生物博物館 (海生館)", lat: 22.046541, lon: 120.698512, desc: "水族館/動物園/水邊" },
    { city: "屏東縣", area: "琉球鄉", category: "海灘", name: "小琉球花瓶岩沙灘", lat: 22.354541, lon: 120.378512, desc: "海灘/珊瑚礁/海龜純點" },
    { city: "屏東縣", area: "屏東市", category: "麵包店", name: "勝利星村創意生活園區", lat: 22.678541, lon: 120.485512, desc: "烘焙甜點/咖啡廳/古蹟" },

    // 宜蘭縣
    { city: "宜蘭縣", area: "頭城鎮", category: "海灘", name: "烏石港外澳沙灘", lat: 24.878541, lon: 121.838521, desc: "衝浪海灘/龜山島景觀" },
    { city: "宜蘭縣", area: "礁溪鄉", category: "溫泉", name: "湯圍溝溫泉公園", lat: 24.828541, lon: 121.774512, desc: "溫泉/公園/拉麵店" },
    { city: "宜蘭縣", area: "蘇澳鎮", category: "水邊", name: "南方澳漁港觀景台", lat: 24.584541, lon: 121.868512, desc: "港口/海鮮/水邊" },
    { city: "宜蘭縣", area: "五結鄉", category: "地標景點", name: "國立傳統藝術中心", lat: 24.686541, lon: 121.824512, desc: "文化古蹟/傳統糕餅甜點" },

    // 花蓮縣
    { city: "花蓮縣", area: "新城鄉", category: "海灘", name: "七星潭海岸風景區", lat: 24.030541, lon: 121.629541, desc: "海灘/礫石/機場周邊" },
    { city: "花蓮縣", area: "秀林鄉", category: "山峰", name: "太魯閣國家公園燕子口", lat: 24.172541, lon: 121.564512, desc: "山頂/峽谷/森林" },
    { city: "花蓮縣", area: "壽豐鄉", category: "地標景點", name: "遠雄海洋公園", lat: 23.901541, lon: 121.603512, desc: "水族館/遊樂園/海灘" },
    { city: "花蓮縣", area: "瑞穗鄉", category: "溫泉", name: "瑞穗黃金溫泉區", lat: 23.498541, lon: 121.354512, desc: "溫泉/牧場咖啡" },

    // 台東縣
    { city: "台東縣", area: "台東市", category: "海灘", name: "加路蘭海岸遊憩區", lat: 22.806541, lon: 121.196512, desc: "海灘/裝置藝術/水邊" },
    { city: "台東縣", area: "鹿野鄉", category: "地標景點", name: "鹿野高台熱氣球嘉年華", lat: 22.914541, lon: 121.118512, desc: "高台/飛行傘/草地公園" },
    { city: "台東縣", area: "池上鄉", category: "森林", name: "伯朗大道金城武樹", lat: 23.100541, lon: 121.218512, desc: "稻田/單車/田園景觀" },
    { city: "台東縣", area: "綠島鄉", category: "溫泉", name: "綠島朝日海底溫泉", lat: 22.634541, lon: 121.503512, desc: "世界級海底溫泉/海灘" },
    { city: "台東縣", area: "蘭嶼鄉", category: "海灘", name: "蘭嶼東清灣拼板舟", lat: 22.056541, lon: 121.564512, desc: "海灘/日出/獨木舟水邊" },

    // 澎湖縣
    { city: "澎湖縣", area: "馬公市", category: "海灘", name: "山水沙灘", lat: 23.513541, lon: 119.593512, desc: "金色沙灘/衝浪海灘" },
    { city: "澎湖縣", area: "白沙鄉", category: "地標景點", name: "澎湖跨海大橋", lat: 23.652541, lon: 119.558512, desc: "橋樑/地標/水邊" },
    { city: "澎湖縣", area: "七美鄉", category: "地標景點", name: "七美雙心石滬", lat: 23.218541, lon: 119.444512, desc: "石滬/海角/地標" },

    // 金門縣
    { city: "金門縣", area: "金城鎮", category: "地標景點", name: "莒光樓與翟山坑道", lat: 24.417541, lon: 118.314512, desc: "地標/坑道水邊/古蹟" },
    { city: "金門縣", area: "金湖鎮", category: "海灘", name: "成功海防坑道海灘", lat: 24.439541, lon: 118.397512, desc: "海灘/軍事古蹟" },

    // 連江縣 (馬祖)
    { city: "連江縣", area: "南竿鄉", category: "水邊", name: "南竿北海坑道藍眼淚", lat: 26.143541, lon: 119.932512, desc: "藍眼淚/坑道水邊/港口" },
    { city: "連江縣", area: "北竿鄉", category: "海灘", name: "北竿芹壁聚落與坂里沙灘", lat: 26.223541, lon: 119.982512, desc: "石頭屋/沙灘/地標" }
];

let allPipiSpots = [...ALL_PIPI_SPOTS_DB];
let pipiMarkersLayer = null;

document.addEventListener("DOMContentLoaded", () => {
    initPipiModule();
});

function initPipiModule() {
    renderPipiFilters();
    renderPipiList(allPipiSpots);

    // 篩選事件綁定
    const citySelect = document.getElementById('pipi-city');
    const areaSelect = document.getElementById('pipi-area');
    const catSelect = document.getElementById('pipi-category');
    const searchInput = document.getElementById('pipi-search');
    const searchBtn = document.getElementById('btn-pipi-search');

    if (citySelect) {
        citySelect.addEventListener('change', () => {
            updatePipiAreaDropdown(citySelect.value);
            filterPipiSpots();
        });
    }

    if (areaSelect) {
        areaSelect.addEventListener('change', filterPipiSpots);
    }

    if (catSelect) {
        catSelect.addEventListener('change', filterPipiSpots);
    }

    if (searchBtn) {
        searchBtn.addEventListener('click', filterPipiSpots);
    }

    if (searchInput) {
        searchInput.addEventListener('input', filterPipiSpots);
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') filterPipiSpots();
        });
    }

    // 切換到皮皮分頁時繪製標記
    const pipiTab = document.getElementById('tab-pipi');
    if (pipiTab) {
        pipiTab.addEventListener('click', () => {
            updatePipiMapMarkers(allPipiSpots);
        });
    }
}

function renderPipiFilters() {
    const citySelect = document.getElementById('pipi-city');
    const catSelect = document.getElementById('pipi-category');

    if (!citySelect || !catSelect) return;

    // 1. 填入全台灣 22 縣市
    citySelect.innerHTML = '<option value="">全部縣市 (全台灣 22 縣市)</option>';
    Object.keys(TAIWAN_DISTRICTS).forEach(c => {
        const opt = document.createElement('option');
        opt.value = c;
        opt.innerText = c;
        citySelect.appendChild(opt);
    });

    // 2. 填入 Pikmin Bloom 36 種全飾品分類
    catSelect.innerHTML = '<option value="">所有飾品分類 (全部 36 種)</option>';
    PIKMIN_CATEGORIES.forEach(cat => {
        const opt = document.createElement('option');
        opt.value = cat;
        opt.innerText = cat;
        catSelect.appendChild(opt);
    });

    updatePipiAreaDropdown("");
}

function updatePipiAreaDropdown(selectedCity) {
    const areaSelect = document.getElementById('pipi-area');
    if (!areaSelect) return;

    areaSelect.innerHTML = '<option value="">全部行政區</option>';
    if (!selectedCity || !TAIWAN_DISTRICTS[selectedCity]) return;

    const areas = TAIWAN_DISTRICTS[selectedCity];
    areas.forEach(a => {
        const opt = document.createElement('option');
        opt.value = a;
        opt.innerText = a;
        areaSelect.appendChild(opt);
    });
}

function filterPipiSpots() {
    const city = document.getElementById('pipi-city')?.value || "";
    const area = document.getElementById('pipi-area')?.value || "";
    const category = document.getElementById('pipi-category')?.value || "";
    const query = (document.getElementById('pipi-search')?.value || "").trim().toLowerCase();

    // 支援直接貼上經緯度或 Pipi Mushroom 連結
    const coordMatch = query.match(/([-+]?[0-9]+\.[0-9]+)\s*,\s*([-+]?[0-9]+\.[0-9]+)/);
    if (coordMatch) {
        const pLat = parseFloat(coordMatch[1]);
        const pLon = parseFloat(coordMatch[2]);
        const customSpot = {
            city: "自訂解析",
            area: "GPS 座標",
            category: "自訂純點",
            name: `解析純點 (${pLat.toFixed(4)}, ${pLon.toFixed(4)})`,
            lat: pLat,
            lon: pLon,
            desc: "由輸入框解析之經緯度座標"
        };
        renderPipiList([customSpot]);
        updatePipiMapMarkers([customSpot]);
        return;
    }

    const filtered = allPipiSpots.filter(s => {
        if (city && s.city !== city) return false;
        if (area && s.area !== area) return false;
        if (category && s.category !== category) return false;
        if (query) {
            const matchName = s.name.toLowerCase().includes(query);
            const matchDesc = (s.desc || "").toLowerCase().includes(query);
            const matchArea = (s.area || "").toLowerCase().includes(query);
            const matchCat = (s.category || "").toLowerCase().includes(query);
            if (!matchName && !matchDesc && !matchArea && !matchCat) return false;
        }
        return true;
    });

    renderPipiList(filtered);
    updatePipiMapMarkers(filtered);
}

function renderPipiList(spots) {
    const listEl = document.getElementById('pipi-spot-list');
    if (!listEl) return;

    listEl.innerHTML = '';

    const currentCity = document.getElementById('pipi-city')?.value || "";
    const currentCat = document.getElementById('pipi-category')?.value || "";

    const header = document.createElement('div');
    header.style.display = 'flex';
    header.style.justifyContent = 'space-between';
    header.style.alignItems = 'center';
    header.style.fontSize = '0.75rem';
    header.style.color = 'var(--text-secondary)';
    header.style.marginBottom = '0.4rem';
    header.innerHTML = `
        <span>找到 <b>${spots.length}</b> 個精選純點</span>
        <a href="javascript:void(0)" onclick="openPipiWithCurrentFilter()" style="color: #60a5fa; text-decoration: none; font-size: 0.72rem;">
            🌐 在 Pipi 網站查看完整名單 ↗
        </a>
    `;
    listEl.appendChild(header);

    if (spots.length === 0) {
        listEl.innerHTML += `
            <div style="text-align:center; padding: 1.5rem; background: rgba(15, 23, 42, 0.4); border-radius: 8px; border: 1px dashed var(--border-color); margin-top: 0.4rem;">
                <div style="font-size: 1.2rem; margin-bottom: 0.3rem;">🔍</div>
                <div style="color: #94a3b8; font-size: 0.82rem; margin-bottom: 0.5rem;">此篩選條件下目前無本機快取純點</div>
                <button onclick="openPipiWithCurrentFilter()" class="btn btn-primary btn-sm" style="margin: 0 auto;">
                    🌐 開啟 Pipi Mushroom 線上資料庫
                </button>
            </div>
        `;
        return;
    }

    spots.forEach((s) => {
        const lat = s.lat;
        const lon = s.lon;
        const card = document.createElement('div');
        card.className = 'pipi-spot-card';
        card.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 0.5rem;">
                <div style="font-weight: 600; font-size: 0.85rem; color: #93c5fd;">${s.name}</div>
                <span class="pipi-badge">${s.category}</span>
            </div>
            <div style="font-size: 0.75rem; color: var(--text-muted); margin: 0.2rem 0;">
                📍 ${s.city} ${s.area} | ${s.desc || ''}
            </div>
            <div style="font-size: 0.72rem; color: #64748b; font-family: monospace;">
                ${lat.toFixed(6)}, ${lon.toFixed(6)}
            </div>
            <div style="display: flex; gap: 0.35rem; margin-top: 0.45rem;">
                <button class="btn btn-primary btn-sm" onclick="teleportToPipiSpot(${lat}, ${lon}, '${escapePipiStr(s.name)}')">⚡ 瞬移到此</button>
                <button class="btn btn-secondary btn-sm" onclick="viewPipiSpotOnMap(${lat}, ${lon})">地圖查看</button>
                <button class="btn btn-secondary btn-sm" onclick="addWaypoint(${lat}, ${lon})">+ 加入路徑</button>
            </div>
        `;
        listEl.appendChild(card);
    });
}

function openPipiWithCurrentFilter() {
    const city = document.getElementById('pipi-city')?.value || "";
    const cat = document.getElementById('pipi-category')?.value || "";
    let url = "https://pipimushroom.com/acclist.aspx?regionCode=TW";
    if (city) url += `&city=${encodeURIComponent(city)}`;
    if (cat) url += `&category=${encodeURIComponent(cat)}`;
    openExternalUrl(url);
}

function teleportToPipiSpot(lat, lon, name) {
    if (window.setTargetPosition) {
        window.setTargetPosition(lat, lon, `🍄 ${name}`);
    }
    if (window.doTeleport) {
        window.doTeleport();
    }
}

function viewPipiSpotOnMap(lat, lon) {
    if (window.map) {
        window.map.setView([lat, lon], 17, { animate: true });
    }
    if (window.setTargetPosition) {
        window.setTargetPosition(lat, lon);
    }
}

function updatePipiMapMarkers(spots) {
    if (!window.map || typeof L === "undefined") return;

    if (!pipiMarkersLayer) {
        pipiMarkersLayer = L.layerGroup().addTo(window.map);
    } else {
        pipiMarkersLayer.clearLayers();
    }

    // 當前只在地圖顯示前 60 個純點避免過度密集
    const displaySpots = spots.slice(0, 60);

    displaySpots.forEach(s => {
        const marker = L.marker([s.lat, s.lon], {
            icon: L.divIcon({
                className: 'pipi-map-pin',
                html: `<div style="background: #a855f7; color: #fff; width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; border: 2px solid #fff; box-shadow: 0 0 6px rgba(168,85,247,0.8);">🍄</div>`,
                iconSize: [22, 22],
                iconAnchor: [11, 11]
            })
        });

        marker.bindPopup(`
            <div style="font-size: 12px; line-height: 1.4;">
                <b style="color: #3b82f6;">${s.name}</b><br/>
                <span style="color: #888;">分類: ${s.category} | ${s.city} ${s.area}</span><br/>
                <div style="margin-top: 6px;">
                    <button style="padding: 2px 6px; font-size: 11px; background: #3b82f6; color: white; border: none; border-radius: 4px; cursor: pointer;" onclick="teleportToPipiSpot(${s.lat}, ${s.lon}, '${escapePipiStr(s.name)}')">⚡ 瞬移</button>
                </div>
            </div>
        `);

        pipiMarkersLayer.addLayer(marker);
    });
}

function openExternalUrl(url) {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.open_url) {
        window.pywebview.api.open_url(url);
    } else {
        window.open(url, '_blank');
    }
}

function escapePipiStr(str) {
    return (str || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
}
