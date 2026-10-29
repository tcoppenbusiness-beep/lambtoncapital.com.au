/* ============================================================
   Lambton Capital — enquiry form engine, LVR calculators,
   header/nav and sticky-bar behaviour.
   Extracted and restyled from the working form prototype.
   ============================================================ */
(function(){
  "use strict";

  /* ---------- CONFIG ---------- */
  var FORM_ENDPOINT = "https://api.web3forms.com/submit";
  var FORM_ACCESS_KEY = "af8e9c26-1c01-45f3-8e06-d1f62c0856d6";
  var DEMO_MODE = false;
  var BOOKING_URL = "https://calendar.app.google/REPLACE-ME";
  var STORAGE_KEY = "lc_enquiry_v1";

  /* ---------- ANALYTICS STUB ---------- */
  function track(name, params){
    try{
      if (window.dataLayer && typeof window.dataLayer.push === "function"){
        window.dataLayer.push(Object.assign({ event: name }, params || {}));
      } else {
        console.log("[track]", name, params || {});
      }
    }catch(e){ console.log("[track:error]", e); }
  }

  function pagePath(){
    try{ return window.location.pathname || "/"; }catch(e){ return "/"; }
  }

  /* ---------- STATE ---------- */
  var state = { branch: null, step: 1, answers: {}, submitted: false };

  function safeSessionGet(){
    try{
      var raw = sessionStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : null;
    }catch(e){ return null; }
  }
  function safeSessionSet(){
    try{ sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ branch: state.branch, step: state.step, answers: state.answers })); }
    catch(e){ /* ignore */ }
  }

  /* ---------- BRANCH DEFINITIONS ---------- */
  var HERO_TILES = [
    "Buy commercial property",
    "Refinance or facility expiry",
    "Buy a business",
    "Working capital or debt restructure",
    "Development or construction",
    "Equipment or vehicles",
    "Something else"
  ];

  var BRANCH_KEY = {
    "Buy commercial property": "A",
    "Refinance or facility expiry": "B",
    "Buy a business": "C",
    "Working capital or debt restructure": "D",
    "Development or construction": "E",
    "Equipment or vehicles": "F",
    "Something else": "G"
  };

  function tilesField(id, label, why, options, opts){
    opts = opts || {};
    return { id: id, type: "tiles", label: label, why: why, options: options, multi: !!opts.multi, required: opts.required !== false };
  }
  function selectField(id, label, why, options){
    return { id: id, type: "select", label: label, why: why, options: options, required: true };
  }
  function showIfMatches(cond){
    var v = state.answers[cond.field];
    return cond.in ? cond.in.indexOf(v) > -1 : v === cond.equals;
  }
  function textField(id, label, why, opts){
    opts = opts || {};
    return { id: id, type: "text", label: label, why: why, required: !!opts.required, placeholder: opts.placeholder || "" };
  }
  function dateField(id, label, why){
    return { id: id, type: "date", label: label, why: why, required: false };
  }
  function textareaField(id, label, why, opts){
    opts = opts || {};
    return { id: id, type: "textarea", label: label, why: why, required: !!opts.required };
  }

  var BRANCHES = {
    A: {
      name: "Buy commercial property",
      totalSteps: 5,
      steps: [
        { title: "The property", fields: [
          tilesField("propertyType", "What type of property?", "LVR (loan-to-value ratio — the loan as a percentage of the property's value) and which lenders will lend vary a lot by property type.", ["Industrial / warehouse","Retail","Office","Medical, childcare or specialised","Mixed-use","Rural or other"]),
          tilesField("occupancy", "Owner-occupied or investment?", "This changes both maximum LVR and which lenders will consider the deal.", ["Owner-occupied","Investment","Both"])
        ]},
        { title: "The numbers", fields: [
          tilesField("priceBand", "Purchase price", "This sets which lenders and loan sizes are realistic.", ["Under $1m","$1m–$2.5m","$2.5m–$5m","$5m–$10m","Over $10m"]),
          tilesField("depositBand", "Deposit available", "Deposit size sets your LVR and affects the interest rate.", ["Under 20%","20–30%","30–40%","Over 40%","Equity in another property"])
        ]},
        { title: "Structure and timing", fields: [
          tilesField("buyingEntity", "Buying entity", "Some lenders won't lend to trusts or SMSFs (self-managed super funds), so this narrows the lenders quickly.", ["Company","Trust","SMSF","Individuals","Not decided"]),
          tilesField("stage", "Where are you at?", "Timing tells us how urgently to move.", ["Researching","Found a property","Offer made","Contract exchanged"])
        ],
          conditional: [
            { showIf: { field: "stage", in: ["Found a property","Offer made","Contract exchanged"] }, field: textField("postcode", "Property postcode", "Helps us match valuers and lenders active in the area.", { required: true, placeholder: "e.g. 2285" }) },
            { showIf: { field: "stage", equals: "Researching" }, field: textField("searchArea", "Where are you looking? (optional)", "A suburb, region or city is enough. We can talk options before you've found a property.", { placeholder: "e.g. Newcastle, Western Sydney" }) },
            { showIf: { field: "stage", equals: "Contract exchanged" }, field: dateField("financeDate", "Finance clause date (the contract deadline to get your loan approved)", "We prioritise deals against the finance clause deadline.") } ]
        }
      ]
    },
    B: {
      name: "Refinance or facility expiry", totalSteps: 5,
      steps: [
        { title: "The loan", fields: [
          tilesField("facilitySize", "Loan size", "Sets the scale of lenders we'll approach.", ["Under $500k","$500k–$1m","$1m–$2.5m","$2.5m–$5m","Over $5m"]),
          tilesField("currentLender", "Current lender", "Tells us which lender you're moving from.", ["Big four bank","Other bank","Non-bank","Private lender"])
        ]},
        { title: "Timing and reason", fields: [
          tilesField("expiry", "When does it expire?", "Expiry timing sets how urgent this is and which lenders can move fast enough.", ["Within 3 months","3–6 months","6–12 months","Over 12 months","Not sure"]),
          tilesField("reason", "Why are you refinancing?", "Select all that apply.", ["Lender raised my rate","Loan expiring","Release equity","Lender asked us to move","Combine loans into one"], { multi: true })
        ]},
        { title: "Security", fields: [
          tilesField("security", "What security can you offer?", "Security is an asset the lender can claim if the loan isn't repaid. The type affects which lenders can help.", ["Commercial property","Residential property","Both","Business assets only"])
        ]}
      ]
    },
    C: {
      name: "Buy a business", totalSteps: 5,
      steps: [
        { title: "The business", fields: [
          tilesField("priceBand", "Purchase price", "Sets the scale of finance required.", ["Under $500k","$500k–$1m","$1m–$3m","$3m–$10m","Over $10m"]),
          selectField("industry", "Industry", "Some lenders specialise or exclude certain industries.", ["Hospitality","Retail","Manufacturing","Professional services","Healthcare","Transport / logistics","Construction / trades","Other"])
        ]},
        { title: "What's included", fields: [
          tilesField("includesProperty", "Does the sale include property?", "Owning the property outright (freehold) changes the security and loan structure a lot.", ["Yes, freehold","No, leasehold or goodwill only"]),
          tilesField("ebitda", "Business EBITDA (earnings before interest, tax, depreciation and amortisation)", "Lenders mainly use this to judge whether the business can afford the repayments.", ["Under $250k","$250k–$500k","$500k–$1m","Over $1m","Not sure"])
        ]},
        { title: "Contribution and stage", fields: [
          tilesField("contribution", "Your contribution (your own money in the deal)", "The more of your own money you put in, the more lender options you usually have.", ["Under 20%","20–30%","30–50%","Over 50%","Vendor finance (seller funds part)"]),
          tilesField("stage", "Where are you at?", "Timing tells us how urgently to move.", ["Looking","In negotiation","Heads of agreement signed","Contract signed"])
        ]}
      ]
    },
    D: {
      name: "Working capital or debt restructure", totalSteps: 5,
      steps: [
        { title: "The loan", fields: [
          tilesField("amount", "Amount needed", "Sets which lenders and products fit.", ["Under $250k","$250k–$500k","$500k–$1m","$1m–$3m","Over $3m"]),
          tilesField("revenue", "Annual revenue", "Working capital is assessed mostly on turnover and cash flow.", ["Under $1m","$1m–$3m","$3m–$10m","Over $10m"])
        ]},
        { title: "Trading history and purpose", fields: [
          tilesField("yearsTrading", "Years trading", "Time trading affects which lenders will consider the deal.", ["Under 2","2–5","Over 5"]),
          tilesField("purpose", "What's it for?", "Select all that apply.", ["Cash-flow gap","Stock or contracts","Consolidate debts","Pay out a partner","Fit-out or expansion"], { multi: true })
        ]},
        { title: "Security and tax position", fields: [
          tilesField("security", "Security available (an asset to back the loan)", "Loans secured against an asset are usually cheaper and faster to arrange.", ["Yes, commercial","Yes, residential","No"]),
          tilesField("atoArrears", "Any overdue tax debt with the ATO (Australian Taxation Office)?", "This must be disclosed early — it doesn't rule you out, but it narrows the lenders who can help.", ["No","Yes, on a plan","Yes, not yet arranged","Prefer to discuss"])
        ]}
      ]
    },
    E: {
      name: "Development or construction", totalSteps: 5,
      steps: [
        { title: "The project", fields: [
          tilesField("projectType", "Project type", "Different lenders specialise in different project types.", ["Industrial units","Residential units or townhouses","Mixed-use","Land subdivision","Single commercial build"]),
          tilesField("totalCost", "Total project cost", "Sets the size of the funding needed.", ["Under $2m","$2m–$5m","$5m–$15m","Over $15m"])
        ]},
        { title: "Land and approvals", fields: [
          tilesField("landStatus", "Land status", "Affects timing and which lenders can fund.", ["Not yet secured","Under contract","Owned outright","Owned with debt"]),
          tilesField("approval", "Council planning approval stage (development approval, or DA)", "Approval stage is a key risk factor for construction lenders.", ["No approval yet","Approval lodged","Approval granted","Construction certificate issued"])
        ]},
        { title: "Presales and track record", fields: [
          tilesField("presales", "Presales achieved (units sold before construction)", "Units sold before construction lower the risk for the lender.", ["None","Some","Over 50%","Not applicable"]),
          tilesField("projectsCompleted", "Projects completed to date", "Track record affects which lenders will lend and the interest rate.", ["First project","1–3","More than 3"])
        ]}
      ]
    },
    F: {
      name: "Equipment or vehicles", totalSteps: 4,
      steps: [
        { title: "The asset", fields: [
          tilesField("assetType", "Asset type", "Different types of asset suit different lenders and loan terms.", ["Truck or trailer","Earthmoving","Vehicles","Machinery","Fit-out or IT","Other"]),
          tilesField("priceBand", "Purchase price", "Sets loan size and likely lender panel.", ["Under $100k","$100k–$250k","$250k–$500k","Over $500k"]),
          tilesField("condition", "New or used?", "Age and condition affect what the asset is worth at the end of the loan, and the interest rate.", ["New","Used"])
        ]},
        { title: "Your business", fields: [
          tilesField("abnAge", "How long have you held your ABN (Australian Business Number)?", "Time trading affects which lenders can help, especially for low-doc loans (assessed on fewer financial documents).", ["Under 1 year","1–2","Over 2"]),
          tilesField("gstRegistered", "GST registered?", "Affects whether you qualify for some low-doc equipment loans.", ["Yes","No"]),
          tilesField("timing", "When do you need funds?", "Tells us how urgently to move.", ["This week","This month","Next 3 months"])
        ]}
      ]
    },
    G: {
      name: "Something else", totalSteps: 3,
      steps: [ { title: "Tell us more", fields: [ textareaField("freeText", "Tell us in a sentence", "So we can point you to the right person straight away.", { required: true }) ] } ]
    }
  };

  var CONTACT_FIELDS = [
    textField("fullName", "Full name", "So we know who we're speaking with.", { required: true }),
    textField("mobile", "Mobile", "We'll call to confirm details before doing anything else.", { required: true, placeholder: "04xx xxx xxx" }),
    textField("email", "Email", "For your written summary and lender documents.", { required: true, placeholder: "name@example.com" }),
    textField("businessName", "Business name (optional)", "Only relevant if the finance is for a business or entity.", { required: false }),
    tilesField("bestTime", "Best time to call", "So we don't chase you at a bad time.", ["Morning","Midday","After 5pm"]),
    textField("notes", "Anything we should know?", "Optional — anything unusual about the deal that helps us prep.", { required: false })
  ];

  /* ---------- DOM helpers ---------- */
  function el(tag, attrs, children){
    var e = document.createElement(tag);
    attrs = attrs || {};
    for (var k in attrs){
      if (k === "class") e.className = attrs[k];
      else if (k === "html") e.innerHTML = attrs[k];
      else if (k === "text") e.textContent = attrs[k];
      else e.setAttribute(k, attrs[k]);
    }
    (children || []).forEach(function(c){ if (c) e.appendChild(c); });
    return e;
  }

  function fmtMoney(n){
    if (isNaN(n) || n === null) return "$0";
    return "$" + Math.round(n).toLocaleString("en-AU");
  }

  /* ---------- TILE BUTTON (box + label, matches design tokens) ---------- */
  function makeTileButton(label, checked, onSelect){
    var text = el("span", {}, [document.createTextNode(label)]);
    var btn = el("button", {
      type: "button", class: "tile", role: "radio",
      "aria-checked": checked ? "true" : "false", "data-value": label
    }, [text]);
    if (checked) btn.classList.add("selected");
    btn.addEventListener("click", function(){ onSelect(label, btn); });
    return btn;
  }

  /* ---------- STEP 1 TILE RENDERING (any #heroTiles element on the page) ---------- */

  /* ---------- STEP-1 TILE ICONS (inline stroke SVG, 1.5px, currentColor) ---------- */
  var TILE_ICONS = {
    "Buy commercial property": '<path d="M3 21h18M5 21V7l7-4 7 4v14M9 21v-6h6v6M9 11h.01M15 11h.01M9 8h.01M15 8h.01"/>',
    "Refinance or facility expiry": '<path d="M21 12a9 9 0 1 1-2.6-6.4M21 4v5h-5M12 7v5l3 2"/>',
    "Buy a business": '<path d="M3 9h18v11a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1zM3 9l2-5h14l2 5M9 13h6M12 9V4"/>',
    "Working capital or debt restructure": '<path d="M4 19V5M4 19h16M8 15l4-5 3 3 5-6M17 7h3v3"/>',
    "Development or construction": '<path d="M3 21h18M6 21V10l6-3 6 3v11M14 21v-4M10 21v-4M3 10h3M12 3v4M9 5l3-2 3 2"/>',
    "Equipment or vehicles": '<path d="M3 16V9h9l3-4h3l2 4h1v7M3 16h18M7 19a2 2 0 1 0 0-4 2 2 0 0 0 0 4zM17 19a2 2 0 1 0 0-4 2 2 0 0 0 0 4z"/>',
    "Something else": '<path d="M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM9.5 9.5a2.5 2.5 0 0 1 5 0c0 1.5-2.5 2-2.5 3.5M12 17h.01"/>'
  };
  function tileIcon(label){
    var d = TILE_ICONS[label];
    if (!d) return null;
    var span = document.createElement("span");
    span.className = "tile-icon";
    span.setAttribute("aria-hidden", "true");
    span.innerHTML = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">' + d + '</svg>';
    return span;
  }
  function renderHeroTilesInto(container){
    if (!container) return;
    container.innerHTML = "";
    var group = el("div", { class: "tile-group", role: "radiogroup", "aria-label": "What is the finance for?" });
    HERO_TILES.forEach(function(label){
      var btn = makeTileButton(label, state.branch === label, function(){ selectBranch(label); });
      var ic = tileIcon(label); if (ic) btn.insertBefore(ic, btn.firstChild);
      group.appendChild(btn);
    });
    var labelText = container.getAttribute("data-label") || "What is the finance for?";
    container.appendChild(el("div", { class: "label", style: "margin-bottom:12px;", text: labelText }));
    container.appendChild(group);
  }

  function renderAllHeroTileGroups(){
    var groups = document.querySelectorAll("[data-hero-tiles]");
    groups.forEach(renderHeroTilesInto);
  }

  function selectBranch(label){
    state.branch = label;
    state.step = 2;
    state.answers = {};
    safeSessionSet();
    track("form_start", { branch: label });
    renderAll();
    var target = document.getElementById("enquiry");
    if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  window.LC = window.LC || {};
  window.LC.selectBranch = selectBranch;

  /* ---------- FORM STEP RENDERING ---------- */
  function renderFormArea(){
    var container = document.getElementById("formSteps");
    if (!container) return;
    container.innerHTML = "";

    if (state.submitted) return;

    if (!state.branch){
      var intro = el("div", { class: "form-step" });
      intro.appendChild(el("div", { class: "form-progress", text: "Step 1 of 5" }));
      intro.appendChild(el("h2", { class: "form-title", text: "What is the finance for?" }));
      var tileWrap = el("div", { "data-hero-tiles": "" });
      intro.appendChild(tileWrap);
      renderHeroTilesInto(tileWrap);
      intro.appendChild(el("p", { class: "why-note", text: "This tells us which questions actually matter for your deal." }));
      container.appendChild(intro);
      return;
    }

    var key = BRANCH_KEY[state.branch];
    var branchDef = BRANCHES[key];
    var isContactStep = state.step === branchDef.totalSteps;
    var stepWrap = el("div", { class: "form-step" });

    stepWrap.appendChild(el("div", { class: "form-progress", text: "Step " + state.step + " of " + branchDef.totalSteps }));

    if (isContactStep){
      stepWrap.appendChild(el("h2", { class: "form-title", text: "Your details" }));
      renderContactStep(stepWrap);
    } else {
      var stepDef = branchDef.steps[state.step - 2];
      stepWrap.appendChild(el("h2", { class: "form-title", text: stepDef.title }));
      stepDef.fields.forEach(function(f){ stepWrap.appendChild(renderField(f)); });
      if (stepDef.conditional){
        stepDef.conditional.forEach(function(c){
          if (showIfMatches(c.showIf)) stepWrap.appendChild(renderField(c.field));
        });
      }
      if (stepDef.extra) stepDef.extra.forEach(function(f){ stepWrap.appendChild(renderField(f)); });
    }

    var nav = el("div", { class: "form-nav" });
    if (state.step > 1){
      var back = el("button", { type: "button", class: "btn btn-secondary", text: "Back" });
      back.addEventListener("click", function(){ goBack(); });
      nav.appendChild(back);
    } else {
      nav.appendChild(el("span"));
    }

    if (isContactStep){
      nav.appendChild(el("button", { type: "submit", class: "btn btn-primary", text: "Send my enquiry" }));
    } else {
      var next = el("button", { type: "button", class: "btn btn-primary", text: "Continue" });
      next.addEventListener("click", function(){ goNext(stepWrap); });
      nav.appendChild(next);
    }
    stepWrap.appendChild(nav);
    container.appendChild(stepWrap);
  }

  function renderField(f){
    var wrap = el("div", { class: "question", id: "q-" + f.id });
    if (f.type === "tiles"){
      wrap.appendChild(el("span", { class: "qlabel", text: f.label }));
      var group = el("div", { class: "tile-group", role: "radiogroup", "aria-label": f.label });
      f.options.forEach(function(opt){
        var current = state.answers[f.id];
        var checked = f.multi ? (Array.isArray(current) && current.indexOf(opt) > -1) : (current === opt);
        var btn = makeTileButton(opt, checked, function(val, btnEl){
          if (f.multi){
            var arr = Array.isArray(state.answers[f.id]) ? state.answers[f.id].slice() : [];
            var idx = arr.indexOf(val);
            if (idx > -1){ arr.splice(idx, 1); btnEl.setAttribute("aria-checked", "false"); btnEl.classList.remove("selected"); }
            else { arr.push(val); btnEl.setAttribute("aria-checked", "true"); btnEl.classList.add("selected"); }
            state.answers[f.id] = arr;
          } else {
            state.answers[f.id] = val;
            var siblings = group.querySelectorAll(".tile");
            siblings.forEach(function(s){
              var on = s === btnEl;
              s.setAttribute("aria-checked", on ? "true" : "false");
              s.classList.toggle("selected", on);
            });
          }
          safeSessionSet();
          clearFieldError(f.id);
          if (f.id === "stage" || f.id === "expiry") renderFormArea();
        });
        group.appendChild(btn);
      });
      wrap.appendChild(group);
    } else if (f.type === "select"){
      wrap.appendChild(el("label", { class: "field-label", for: "f-" + f.id, text: f.label }));
      var sel = el("select", { id: "f-" + f.id });
      sel.appendChild(el("option", { value: "", text: "Select…" }));
      f.options.forEach(function(opt){
        var o = el("option", { value: opt, text: opt });
        if (state.answers[f.id] === opt) o.selected = true;
        sel.appendChild(o);
      });
      sel.addEventListener("change", function(){ state.answers[f.id] = sel.value; safeSessionSet(); clearFieldError(f.id); });
      wrap.appendChild(sel);
    } else if (f.type === "text"){
      wrap.appendChild(el("label", { class: "field-label", for: "f-" + f.id, text: f.label }));
      var inp = el("input", { type: "text", id: "f-" + f.id, placeholder: f.placeholder || "" });
      inp.value = state.answers[f.id] || "";
      inp.addEventListener("input", function(){ state.answers[f.id] = inp.value; safeSessionSet(); });
      inp.addEventListener("blur", function(){ validateSimpleField(f, inp.value); });
      wrap.appendChild(inp);
      wrap.appendChild(el("p", { class: "field-err", id: "err-" + f.id }));
    } else if (f.type === "date"){
      wrap.appendChild(el("label", { class: "field-label", for: "f-" + f.id, text: f.label }));
      var d = el("input", { type: "date", id: "f-" + f.id });
      d.value = state.answers[f.id] || "";
      d.addEventListener("change", function(){ state.answers[f.id] = d.value; safeSessionSet(); });
      wrap.appendChild(d);
    } else if (f.type === "textarea"){
      wrap.appendChild(el("label", { class: "field-label", for: "f-" + f.id, text: f.label }));
      var ta = el("textarea", { id: "f-" + f.id, rows: "3" });
      ta.value = state.answers[f.id] || "";
      ta.addEventListener("input", function(){ state.answers[f.id] = ta.value; safeSessionSet(); });
      wrap.appendChild(ta);
      wrap.appendChild(el("p", { class: "field-err", id: "err-" + f.id }));
    }
    if (f.why) wrap.appendChild(el("p", { class: "why-note", text: "Why we ask: " + f.why }));
    return wrap;
  }

  function clearFieldError(id){
    var e = document.getElementById("err-" + id);
    if (e) e.textContent = "";
  }

  function validateSimpleField(f, value){
    var errEl = document.getElementById("err-" + f.id);
    if (!errEl) return true;
    if (f.required && !value.trim()){ errEl.textContent = "This field is required."; return false; }
    if (f.id === "mobile" && value.trim()){
      var digits = value.replace(/\s+/g, "");
      var ok = /^04\d{8}$/.test(digits) || /^\+614\d{8}$/.test(digits);
      if (!ok){ errEl.textContent = "Enter a valid Australian mobile, e.g. 04xx xxx xxx."; return false; }
    }
    if (f.id === "email" && value.trim()){
      var okEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
      if (!okEmail){ errEl.textContent = "Enter a valid email address."; return false; }
    }
    errEl.textContent = "";
    return true;
  }

  function renderContactStep(stepWrap){
    CONTACT_FIELDS.forEach(function(f){ stepWrap.appendChild(renderField(f)); });
    stepWrap.appendChild(el("p", { class: "privacy-line", html: 'We collect this to assess your enquiry and may share it with lenders. See our <a href="#privacy">Privacy Policy</a>.' }));

    var checkRow = el("div", { class: "checkbox-row" });
    var cb = el("input", { type: "checkbox", id: "f-consent" });
    cb.checked = !!state.answers.consent;
    cb.addEventListener("change", function(){ state.answers.consent = cb.checked; safeSessionSet(); clearFieldError("consent"); });
    checkRow.appendChild(cb);
    checkRow.appendChild(el("label", { for: "f-consent", text: "I agree to be contacted about this enquiry" }));
    stepWrap.appendChild(checkRow);
    stepWrap.appendChild(el("p", { class: "field-err", id: "err-consent" }));
  }

  function validateStep(fields, isContact){
    var valid = true;
    fields.forEach(function(f){
      if (f.type === "text" || f.type === "textarea"){
        var v = state.answers[f.id] || "";
        if (!validateSimpleField(f, v)) valid = false;
      }
      if (f.type === "tiles" && f.required !== false){
        var current = state.answers[f.id];
        var has = f.multi ? (Array.isArray(current) && current.length > 0) : !!current;
        if (!has) valid = false;
      }
      if (f.type === "select" && f.required){ if (!state.answers[f.id]) valid = false; }
    });
    if (isContact){
      var errEl = document.getElementById("err-consent");
      if (!state.answers.consent){ if (errEl) errEl.textContent = "Please tick this box to continue."; valid = false; }
    }
    return valid;
  }

  function goNext(){
    var key = BRANCH_KEY[state.branch];
    var branchDef = BRANCHES[key];
    var stepDef = branchDef.steps[state.step - 2];
    var fields = stepDef.fields.slice();
    if (stepDef.extra) fields = fields.concat(stepDef.extra);
    if (stepDef.conditional){
      stepDef.conditional.forEach(function(c){ if (showIfMatches(c.showIf)) fields.push(c.field); });
    }
    if (!validateStep(fields, false)) return;
    state.step += 1;
    safeSessionSet();
    track("form_step_" + state.step, { branch: state.branch, step: state.step });
    renderFormArea();
    scrollFormIntoView();
  }

  function goBack(){
    if (state.step <= 1) return;
    if (state.step === 2){ state.branch = null; state.step = 1; state.answers = {}; }
    else { state.step -= 1; }
    safeSessionSet();
    renderAll();
    scrollFormIntoView();
  }

  function scrollFormIntoView(){
    var section = document.getElementById("enquiry");
    if (section) section.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  /* ---------- SCORING ---------- */
  function computeScore(){
    var score = 0, specialist = false, a = state.answers, allValues = [];
    for (var k in a){
      if (Array.isArray(a[k])) allValues = allValues.concat(a[k]);
      else if (a[k]) allValues.push(String(a[k]));
    }
    var joined = allValues.join(" | ");
    function has(str){ return joined.indexOf(str) > -1; }

    if (has("$2.5m–$5m") || has("Over $10m") || has("$5m–$10m") || has("$5m–$15m") || has("Over $15m") || has("Over $5m") || has("Over $3m") || has("$3m–$10m")) score += 30;
    else if (has("$1m–$2.5m") || has("$1m–$3m") || has("$2m–$5m")) score += 20;
    else if (has("$500k–$1m") || has("Under $1m")) score += 10;

    if (has("Contract exchanged") || has("Contract signed") || has("Within 3 months")) score += 30;
    else if (has("Offer made") || has("Heads of agreement signed") || has("3–6 months")) score += 20;

    if (has("30–40%") || has("Over 40%") || has("Owner-occupied") || has("30–50%") || has("Over 50%")) score += 10;

    if (has("Lender asked us to move")){ score -= 10; specialist = true; }
    if (has("Yes, not yet arranged")){ score -= 10; specialist = true; }
    if (has("First project")){ score -= 10; specialist = true; }
    if (has("Under 2")){ score -= 10; specialist = true; }

    var tier = "D-REDIRECT";
    if (score >= 60) tier = "A-HOT";
    else if (score >= 35) tier = "B-QUAL";
    else if (score >= 15) tier = "C-NURTURE";

    if (state.branch === "Equipment or vehicles"){
      var order = ["A-HOT","B-QUAL","C-NURTURE","D-REDIRECT"];
      if (order.indexOf(tier) < order.indexOf("C-NURTURE")) tier = "C-NURTURE";
    }
    return { score: score, tier: tier, specialist: specialist };
  }

  function buildSubject(scoring){
    var a = state.answers;
    var parts = [ "[" + scoring.tier + "]" ];
    parts.push(state.branch || "Enquiry");
    if (a.priceBand) parts.push(a.priceBand);
    else if (a.totalCost) parts.push(a.totalCost);
    else if (a.amount) parts.push(a.amount);
    else if (a.facilitySize) parts.push(a.facilitySize);
    if (a.stage) parts.push(a.stage);
    else if (a.expiry) parts.push(a.expiry);
    parts.push(pagePath());
    var subject = parts.join(" · ");
    if (scoring.specialist) subject += " · SPECIALIST";
    return subject;
  }

  function getQueryParam(name){
    try{ var params = new URLSearchParams(window.location.search); return params.get(name) || ""; }
    catch(e){ return ""; }
  }

  function buildHiddenFields(scoring){
    return {
      page_path: pagePath(), branch: state.branch || "",
      utm_source: getQueryParam("utm_source"), utm_medium: getQueryParam("utm_medium"),
      utm_campaign: getQueryParam("utm_campaign"), utm_term: getQueryParam("utm_term"),
      gclid: getQueryParam("gclid"),
      referrer: (typeof document !== "undefined" ? document.referrer : ""),
      score: scoring.score, tier: scoring.tier, specialist: scoring.specialist,
      timestamp: new Date().toISOString(), form_version: "1.0"
    };
  }

  /* ---------- SUBMIT ---------- */
  function handleSubmit(ev){
    ev.preventDefault();
    if (!validateStep(CONTACT_FIELDS, true)) return;

    var honeypot = document.getElementById("botcheck");
    if (honeypot && honeypot.value) return;

    var scoring = computeScore();
    var subject = buildSubject(scoring);
    var hidden = buildHiddenFields(scoring);
    var payload = Object.assign({ access_key: FORM_ACCESS_KEY, subject: subject, from_name: state.answers.fullName || "Website enquiry" }, state.answers, hidden);

    track("form_submit", { branch: state.branch, tier: scoring.tier, score: scoring.score });

    if (DEMO_MODE){ showThankYou(payload); return; }

    fetch(FORM_ENDPOINT, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload)
    }).then(function(res){
      if (!res.ok) throw new Error("Network response was not ok");
      showThankYou(payload);
    }).catch(function(err){
      console.log("[submit:error]", err);
      var errBox = document.getElementById("submitError");
      if (!errBox){
        errBox = el("p", { id: "submitError", class: "field-err", text: "Something went wrong sending your enquiry. Please try again." });
        var f = document.getElementById("enquiryForm");
        if (f) f.appendChild(errBox);
      }
    });
  }

  function showThankYou(payload){
    state.submitted = true;
    try{ sessionStorage.removeItem(STORAGE_KEY); }catch(e){}
    var formEl = document.getElementById("enquiryForm");
    if (formEl) formEl.style.display = "none";
    var ty = document.getElementById("thankyou");
    if (!ty) return;
    ty.style.display = "block";
    ty.innerHTML = "";
    ty.appendChild(el("h2", { class: "h2", text: "Your enquiry is in." }));
    ty.appendChild(el("p", { class: "lead", text: "Thanks. We'll reply in writing within two business days. Deal assessments open once our lender panel is confirmed, and early enquiries are contacted first." }));
    var actions = el("div", { class: "thankyou-actions" });
    if (BOOKING_URL.indexOf("REPLACE-ME") === -1){
    var bookBtn = el("a", { class: "btn btn-primary", href: BOOKING_URL, target: "_blank", rel: "noopener noreferrer", text: "Book a 20-minute discovery call" });
    bookBtn.addEventListener("click", function(){ track("booking_click", { branch: state.branch }); });
    actions.appendChild(bookBtn);
    ty.appendChild(actions);
    }
    ty.appendChild(el("p", { class: "body-sm", html: '<a href="' + relativeTo("thank-you.html") + '">See the confirmation page</a> · <a href="' + relativeTo("fees.html") + '">How our fees work</a>' }));

  }

  /* Resolve a root-relative asset name against how deep the current page sits. */
  function relativeTo(name){
    var depth = document.body.getAttribute("data-depth");
    depth = depth ? parseInt(depth, 10) : 0;
    var prefix = "";
    for (var i = 0; i < depth; i++) prefix += "../";
    return prefix + name;
  }

  /* ============================================================
     LVR CALCULATORS
     ============================================================ */
  var LVR_BANDS = {
    "Industrial": 0.70,
    "Retail": 0.65,
    "Office": 0.65,
    "Medical/childcare": 0.65,
    "Specialised": 0.55
  };
  var ASSUMED_RATE = 0.075; /* indicative interest-only rate used for ICR estimate, general information only */

  function parseMoney(v){
    var n = parseFloat(String(v).replace(/[^0-9.]/g, ""));
    return isNaN(n) ? 0 : n;
  }

  /* Basic calculator: property type + purchase price -> max lend + deposit, with an email gate.
     Looks for elements scoped inside `root` using data-calc-* attributes. */
  function initBasicCalc(root){
    if (!root) return;
    var typeSel = root.querySelector("[data-calc-type]");
    var priceInp = root.querySelector("[data-calc-price]");
    var lendOut = root.querySelector("[data-calc-lend]");
    var depositOut = root.querySelector("[data-calc-deposit]");
    if (!typeSel || !priceInp || !lendOut || !depositOut) return;

    function lvrFor(val){ return LVR_BANDS[val] !== undefined ? LVR_BANDS[val] : parseFloat(val) || 0; }

    function recalc(){
      var lvr = lvrFor(typeSel.value);
      var price = parseMoney(priceInp.value);
      var lend = price * lvr;
      var deposit = price - lend;
      lendOut.textContent = fmtMoney(lend);
      depositOut.textContent = fmtMoney(deposit);
    }
    typeSel.addEventListener("change", recalc);
    priceInp.addEventListener("input", recalc);
    recalc();

    initEmailGate(root);
  }

  /* Extended calculator (Tools page): adds owner-occupied toggle and rent/EBITDA -> indicative ICR. */
  function initExtendedCalc(root){
    if (!root) return;
    var typeSel = root.querySelector("[data-calc-type]");
    var priceInp = root.querySelector("[data-calc-price]");
    var ownerBox = root.querySelector("[data-calc-owner]");
    var rentInp = root.querySelector("[data-calc-rent]");
    var lendOut = root.querySelector("[data-calc-lend]");
    var depositOut = root.querySelector("[data-calc-deposit]");
    var icrOut = root.querySelector("[data-calc-icr]");
    if (!typeSel || !priceInp || !lendOut || !depositOut) return;

    function lvrFor(val){ return LVR_BANDS[val] !== undefined ? LVR_BANDS[val] : parseFloat(val) || 0; }

    function recalc(){
      var lvr = lvrFor(typeSel.value);
      if (ownerBox && ownerBox.checked) lvr = Math.min(lvr + 0.05, 0.80);
      var price = parseMoney(priceInp.value);
      var lend = price * lvr;
      var deposit = price - lend;
      lendOut.textContent = fmtMoney(lend);
      depositOut.textContent = fmtMoney(deposit);
      if (icrOut){
        var rent = rentInp ? parseMoney(rentInp.value) : 0;
        var annualInterest = lend * ASSUMED_RATE;
        var icr = annualInterest > 0 ? (rent / annualInterest) : 0;
        icrOut.textContent = icr > 0 ? (Math.round(icr * 10) / 10).toFixed(1) + "x" : "—";
      }
    }
    typeSel.addEventListener("change", recalc);
    priceInp.addEventListener("input", recalc);
    if (ownerBox) ownerBox.addEventListener("change", recalc);
    if (rentInp) rentInp.addEventListener("input", recalc);
    recalc();

    initEmailGate(root);
  }


  /* Full commercial loan calculator (tools/commercial-loan-calculator.html).
     Adds interest rate, term, repayment type, income (interest cover) limit and facility-expiry timing.
     No default rate is applied: repayments and income limit stay blank until a rate is entered. */
  var ICR_HURDLE = 1.75; /* assumed minimum interest cover lenders look for; lender policies vary */

  function initLoanCalc(root){
    if (!root) return;
    function q(a){ return root.querySelector("[" + a + "]"); }
    var typeSel = q("data-calc-type"), priceInp = q("data-calc-price"), ownerBox = q("data-calc-owner"),
        rentInp = q("data-calc-rent"), rateInp = q("data-calc-rate"), termInp = q("data-calc-term"),
        repaySel = q("data-calc-repay"), expiryInp = q("data-calc-expiry");
    var lendOut = q("data-calc-lend"), limitOut = q("data-calc-limit"), depositOut = q("data-calc-deposit"),
        payOut = q("data-calc-payment"), icrOut = q("data-calc-icr"), rateHint = q("data-calc-rate-note"),
        expiryRows = q("data-calc-expiry-rows"), startOut = q("data-calc-start-by"),
        daysOut = q("data-calc-days"), expStatus = q("data-calc-expiry-status");
    if (!typeSel || !priceInp || !lendOut || !depositOut) return;

    var last = {};

    function lvrFor(val){ return LVR_BANDS[val] !== undefined ? LVR_BANDS[val] : parseFloat(val) || 0; }
    function fmtDate(d){ return d.toLocaleDateString("en-AU", { day: "numeric", month: "long", year: "numeric" }); }
    function isoDate(d){
      var m = d.getMonth() + 1, day = d.getDate();
      return d.getFullYear() + "-" + (m < 10 ? "0" : "") + m + "-" + (day < 10 ? "0" : "") + day;
    }

    function recalc(){
      var lvr = lvrFor(typeSel.value);
      if (ownerBox && ownerBox.checked) lvr = Math.min(lvr + 0.05, 0.80);
      var price = parseMoney(priceInp.value);
      var income = rentInp ? parseMoney(rentInp.value) : 0;
      var ratePct = rateInp && rateInp.value !== "" ? parseFloat(rateInp.value) : NaN;
      var hasRate = !isNaN(ratePct) && ratePct >= 0;
      var termYears = termInp ? parseFloat(termInp.value) : NaN;
      if (isNaN(termYears) || termYears <= 0) termYears = 15;
      var interestOnly = repaySel && repaySel.value === "io";

      var lvrLimit = price * lvr;
      var loan = lvrLimit, limitedBy = "Limited by LVR";
      if (hasRate && ratePct > 0 && income > 0){
        var incomeLimit = income / ((ratePct / 100) * ICR_HURDLE);
        if (incomeLimit < lvrLimit){ loan = incomeLimit; limitedBy = "Limited by income (interest cover)"; }
      }
      loan = Math.max(0, loan);
      var deposit = Math.max(0, price - loan);

      var payment = null;
      if (hasRate && loan > 0){
        var r = ratePct / 100 / 12, n = Math.round(termYears * 12);
        if (interestOnly) payment = loan * r;
        else if (r === 0) payment = loan / n;
        else payment = loan * r / (1 - Math.pow(1 + r, -n));
      }
      var icr = null;
      if (hasRate && ratePct > 0 && income > 0 && loan > 0) icr = income / (loan * ratePct / 100);

      lendOut.textContent = fmtMoney(loan);
      if (limitOut) limitOut.textContent = limitedBy;
      depositOut.textContent = fmtMoney(deposit);
      if (payOut) payOut.textContent = payment === null ? "\u2014" : fmtMoney(payment) + " / month";
      if (icrOut) icrOut.textContent = icr === null ? "\u2014" : icr.toFixed(2) + "\u00d7";
      if (rateHint) rateHint.hidden = hasRate;

      /* Facility expiry */
      var expiryIso = "", expiryMsg = "";
      var ev = expiryInp ? expiryInp.value : "";
      var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(ev);
      if (expiryRows) expiryRows.hidden = !m;
      if (m){
        var expiry = new Date(+m[1], +m[2] - 1, +m[3]);
        var now = new Date(); var today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        var startBy = new Date(expiry.getTime()); startBy.setMonth(startBy.getMonth() - 6);
        var days = Math.round((expiry - today) / 86400000);
        expiryIso = isoDate(expiry);
        if (startOut) startOut.textContent = fmtDate(startBy);
        if (days < 0){ expiryMsg = "Expired"; if (daysOut) daysOut.textContent = "Expired"; }
        else {
          if (daysOut) daysOut.textContent = days + (days === 1 ? " day" : " days");
          expiryMsg = startBy <= today ? "Under 6 months \u2014 start now" : "On track \u2014 start by " + fmtDate(startBy);
        }
        if (expStatus){
          expStatus.textContent = expiryMsg;
          expStatus.classList.toggle("calc-urgent", days < 0 || startBy <= today);
        }
      }

      last = {
        property_type: typeSel.value, owner_occupied: !!(ownerBox && ownerBox.checked),
        value: Math.round(price), income: Math.round(income),
        rate_pct: hasRate ? ratePct : "", term_years: termYears,
        repayment_type: interestOnly ? "interest_only" : "principal_and_interest",
        max_loan: Math.round(loan), limited_by: limitedBy, deposit: Math.round(deposit),
        monthly_repayment: payment === null ? "" : Math.round(payment),
        icr: icr === null ? "" : Math.round(icr * 100) / 100,
        expiry_date: expiryIso, expiry_status: expiryMsg
      };
    }

    [typeSel, repaySel, ownerBox, expiryInp].forEach(function(el){ if (el) el.addEventListener("change", recalc); });
    [priceInp, rentInp, rateInp, termInp, expiryInp].forEach(function(el){ if (el) el.addEventListener("input", recalc); });
    recalc();

    var gate = document.querySelector("[data-loan-gate]");
    if (gate) initEmailGate(gate, function(){ recalc(); return last; });
  }

  function initEmailGate(root, payloadFn){
    var emailBtn = root.querySelector("[data-calc-email-btn]");
    var gate = root.querySelector("[data-calc-gate]");
    if (emailBtn && gate){
      emailBtn.addEventListener("click", function(){ gate.classList.add("open"); });
    }
    var checkGroup = root.querySelector("[data-calc-broker-check]");
    if (checkGroup){
      checkGroup.querySelectorAll(".tile").forEach(function(btn){
        btn.addEventListener("click", function(){
          checkGroup.querySelectorAll(".tile").forEach(function(s){
            var on = s === btn;
            s.setAttribute("aria-checked", on ? "true" : "false");
            s.classList.toggle("selected", on);
          });
        });
      });
    }
    var form = root.querySelector("[data-calc-form]");
    if (form){
      form.addEventListener("submit", function(ev){
        ev.preventDefault();
        var successNote = root.querySelector("[data-calc-success]");
        var errNote = root.querySelector("[data-calc-error]");
        var payload = {};
        try { if (typeof payloadFn === "function") payload = payloadFn() || {}; } catch (e) { payload = {}; }
        var fnEl = root.querySelector("#fn"), emEl = root.querySelector("#em"), consentEl = root.querySelector("[data-calc-consent]");
        var firstName = fnEl ? fnEl.value.trim() : "", email = emEl ? emEl.value.trim() : "";
        var brokerSel = root.querySelector("[data-calc-broker-check] .tile[aria-checked='true']");
        var wantsBroker = brokerSel ? brokerSel.textContent.trim() : "Not answered";
        var botEl = document.getElementById("botcheck");
        if (!firstName || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email) || (consentEl && !consentEl.checked)){
          if (errNote) errNote.hidden = false;
          return;
        }
        if (errNote) errNote.hidden = true;
        if (botEl && botEl.checked) return;
        // Analytics gets the calculation only - never name or email
        track("calc_email_result", payload);
        if (DEMO_MODE){ if (successNote) successNote.classList.add("show"); return; }
        var body = Object.assign({
          access_key: FORM_ACCESS_KEY,
          subject: "Calculator result request - " + firstName + (wantsBroker === "Yes" ? " (wants broker check)" : ""),
          from_name: firstName,
          name: firstName,
          email: email,
          wants_broker_check: wantsBroker,
          consent: "Yes",
          source_page: location.pathname
        }, payload);
        fetch(FORM_ENDPOINT, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
          .then(function(res){ if (!res.ok) throw new Error("Network response was not ok"); if (successNote) successNote.classList.add("show"); })
          .catch(function(err){ console.log("[calc-submit:error]", err); if (errNote){ errNote.textContent = "Something went wrong sending your result. Please try again."; errNote.hidden = false; } });
      });
    }
  }

  /* ============================================================
     STICKY MOBILE BAR
     ============================================================ */
  function initStickyBar(){
    var bar = document.getElementById("stickyBar");
    var form = document.getElementById("enquiry");
    if (!bar || !form) return;
    var cta = document.getElementById("stickyCta");
    if (cta){
      cta.textContent = "Get a deal assessment";
      cta.setAttribute("data-cta", "sticky");
      if (!bar.querySelector(".sticky-sub")){
        var sub = document.createElement("p"); sub.className = "sticky-sub";
        sub.textContent = "About 2 minutes \u00b7 No obligation";
        bar.appendChild(sub);
      }
    }
    bar.classList.add("eligible");
    var hero = document.querySelector(".hero-home, .hero, main > section");
    function onScroll(){
      var heroGone = hero ? hero.getBoundingClientRect().bottom < 0 : (window.scrollY > 400);
      var fr = form.getBoundingClientRect();
      var formInView = fr.top < window.innerHeight && fr.bottom > 0;
      if (heroGone && !formInView){ bar.classList.add("visible"); }
      else { bar.classList.remove("visible"); }
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    onScroll();
  }

  function initCtaTracking(){
    document.querySelectorAll('a[href="#enquiry"]').forEach(function(a){
      a.addEventListener("click", function(){
        track("cta_click", { position: a.getAttribute("data-cta") || "other", page_path: pagePath() });
      });
    });
  }

  function initReassurance(){
    var panel = document.querySelector("#enquiry .form-panel");
    if (!panel || panel.querySelector(".form-reassure")) return;
    var p = document.createElement("p"); p.className = "form-reassure";
    var priv = (location.pathname.indexOf("/lp/") > -1 || location.pathname.indexOf("/tools/") > -1) ? "../privacy.html" : "privacy.html";
    p.innerHTML = "<span>About 2 minutes</span><span>No obligation</span><span>No credit check at this stage</span><span><a href=\"" + priv + "\">How we handle your details</a></span>";
    panel.insertBefore(p, panel.firstChild);
  }

  /* ============================================================
     MOBILE NAV TOGGLE
     ============================================================ */
  function initMobileNav(){
    var toggle = document.getElementById("navToggle");
    var menu = document.getElementById("mobileNav");
    if (!toggle || !menu) return;
    toggle.addEventListener("click", function(){
      var open = menu.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  /* ---------- RESTORE / INIT ---------- */
  function restoreState(){
    var saved = safeSessionGet();
    if (saved && saved.branch){
      state.branch = saved.branch;
      state.step = saved.step || 2;
      state.answers = saved.answers || {};
    }
  }

  function renderAll(){
    renderAllHeroTileGroups();
    renderFormArea();
  }

  document.addEventListener("DOMContentLoaded", function(){
    initMobileNav();
    initStickyBar();
    initCtaTracking();
    initReassurance();

    if (document.getElementById("formSteps")){
      restoreState();
      renderAll();
      var form = document.getElementById("enquiryForm");
      if (form) form.addEventListener("submit", handleSubmit);
    } else {
      /* pages with only a stray hero tile group but no full form (none currently) */
      renderAllHeroTileGroups();
    }

    document.querySelectorAll("[data-lvr-basic]").forEach(initBasicCalc);
    document.querySelectorAll("[data-lvr-extended]").forEach(initExtendedCalc);
    document.querySelectorAll("[data-lvr-gate]").forEach(function(g){ initEmailGate(g); });
    document.querySelectorAll("[data-loan-calc]").forEach(initLoanCalc);

    /* Single pre-set tile used on the SMSF page sidebar */
    document.querySelectorAll("[data-select-branch]").forEach(function(btn){
      btn.addEventListener("click", function(){ selectBranch(btn.getAttribute("data-select-branch")); });
    });
  });
})();

// Finance types dropdown: click/keyboard toggle (hover handled in CSS)
(function(){
  var dd = document.querySelector(".nav-dd"); if (!dd) return;
  var btn = dd.querySelector(".nav-dd-btn");
  btn.addEventListener("click", function(){ var o = dd.classList.toggle("open"); btn.setAttribute("aria-expanded", o ? "true" : "false"); });
  document.addEventListener("click", function(e){ if (!dd.contains(e.target)) { dd.classList.remove("open"); btn.setAttribute("aria-expanded","false"); } });
  document.addEventListener("keydown", function(e){ if (e.key === "Escape") { dd.classList.remove("open"); btn.setAttribute("aria-expanded","false"); } });
})();
