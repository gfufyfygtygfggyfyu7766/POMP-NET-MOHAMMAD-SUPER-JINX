/* ===================================================================
   Super JinX · Donation page config  (the ONLY place addresses live)
   - Each address is checked with its network's real checksum before it
     is shown (EIP-55 / Bech32 / Base58Check / TON CRC16).
   - A wrong or mistyped address is hidden automatically, never shown.
   - kind: evm | btc | tron | ton      color: #RRGGBB
   =================================================================== */
var JINX_DONATE = {
  brand: "POMP NET MOHAMMAD",
  edition: "SUPER JINX",
  supportName: "آقای محمدی",
  bankCard: "6280231311605819",
  bankIntro: "هر بخش از POMP NET با تلاش و پیگیری ساخته می‌شود؛ اگر این مسیر برایت مفید بوده، حمایت داوطلبانه‌ات کمک می‌کند پروژه مستقل بماند، امکانات تازه بگیرد و با کیفیت بهتر ادامه پیدا کند. این کارت به نام و برای حمایت از آقای محمدی ثبت شده است. از اعتمادت و همراهی ارزشمندت صمیمانه ممنونیم.",
  supportTelegram: "https://t.me/NovaTunneli",
  channel: "https://t.me/pompnet",
  intro: "قدرت ساخت، آزادی انتخاب، کنترل در دستان تو؛ اگر این مسیر برایت مفید بوده، همراهی تو به ادامه‌ی توسعه‌ی POMP NET جان می‌دهد.",
  intro_en: "If this project has been useful to you, you can help its development and improvement continue with a donation.",
  coins: [
    { id: "bnb",  name: "BNB",      symbol: "BNB",  network: "BNB Smart Chain", standard: "BEP20", kind: "evm",  color: "#F3BA2F", address: "0x2cb214Cbcf48cf5f4C98abcCD5B261eFD166adf2" },
    { id: "btc",  name: "Bitcoin",  symbol: "BTC",  network: "Bitcoin",         standard: "SegWit", kind: "btc", color: "#F7931A", address: "bc1qfellrpfvafzwglhaxa0eq8hjc6l3ls6v2ge3su" },
    { id: "trx",  name: "TRON",     symbol: "TRX",  network: "TRON",            standard: "TRC20", kind: "tron", color: "#EB0029", address: "TEarnfuiKVqmPRNtZE8WjhRaVAX3miAYFz" },
    { id: "gram", name: "Gram",     symbol: "GRAM", network: "TON",             standard: "TON",   kind: "ton",  color: "#0098EA", address: "UQCmiqLPC6lzyFbPLHDRioTupbD-_xObi4koOdAPJMVBmXDd" },
    { id: "usdt", name: "Tether",   symbol: "USDT", network: "BNB Smart Chain", standard: "BEP20", kind: "evm",  color: "#26A17B", address: "0x2cb214Cbcf48cf5f4C98abcCD5B261eFD166adf2" },
    { id: "eth",  name: "Ethereum", symbol: "ETH",  network: "Ethereum",        standard: "ERC20", kind: "evm",  color: "#627EEA", address: "0x3128bc706Ea901669a3ef396BbfB5686Cee53b3f" }
  ]
};
