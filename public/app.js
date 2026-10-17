"use strict";
/* Public Shabbat Calendar viewer. All religious dates come from calendar.json;
   the UI only lays out ordinary Gregorian months and never projects moons. */
(() => {
  const MONTHS=["January","February","March","April","May","June","July","August","September","October","November","December"];
  const WEEKDAYS=["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
  const byId=id=>document.getElementById(id);
  const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n};
  const dt=s=>new Date(s+"T12:00:00Z");
  const iso=d=>d.toISOString().slice(0,10);
  const createDate=(y,m,d)=>new Date(Date.UTC(y,m,d,12));
  const fmt=s=>dt(s).toLocaleDateString("en-US",{timeZone:"UTC",month:"long",day:"numeric",year:"numeric"});
  const getToday=()=>{
    const d=new Date();return [d.getFullYear(),d.getMonth(),d.getDate()];
  };
  const hasEvents=(e,kind)=>e.some(x=>x.kind===kind);
  const kinds=["new_moon","sabbath","feast","preparation"];
  const kindClass={new_moon:"moon",sabbath:"sabbath",feast:"feast",preparation:"prep"};
  const kindName={new_moon:"New Moon",sabbath:"Shabbat",feast:"Draft Feast",preparation:"Preparation"};
  const state={data:null,track:"earlier",selected:null,year:2027,month:2};
  let dayEvents=new Map();

  function eventsIndex(track){
    const d=new Map();
    for(const e of [...(track.current_events||[]),...track.events]){
      if(!d.has(e.date))d.set(e.date,[]);
      d.get(e.date).push(e);
    }
    return d;
  }
  function monthOn(track,day){
    return [...(track.current_months||[]),...track.months].find(m=>m.start<=day&&m.end>=day);
  }
  function yearOn(track,day){
    return track.years.find(y=>y.start_date<=day&&y.next_start_date>day);
  }
  function firstDayOf(month,year){
    const first=createDate(year,month,1),begin=first.getUTCDay();
    const count=createDate(year,month+1,0).getUTCDate();
    const squares=Math.ceil((begin+count)/7)*7;
    return Array.from({length:squares},(_,i)=>{
      const d=createDate(year,month,1-begin+i);
      return {iso:iso(d),day:d.getUTCDate(),inMonth:d.getUTCMonth()===month};
    });
  }
  function todayIso(){return iso(createDate(...getToday()))}
  function nextShabbat(track){
    const current=todayIso();
    return [...(track.current_events||[]),...track.events]
      .filter(e=>e.kind==="sabbath"&&e.date>=current)
      .sort((a,b)=>a.date.localeCompare(b.date))[0]||null;
  }
  function renderUpNext(track){
    const target=byId("up-next"),next=nextShabbat(track);
    target.replaceChildren();
    target.hidden=!next;
    if(!next)return;
    target.append(node("span","UP NEXT · SHABBAT","up-next-label"));
    target.append(node("strong",fmt(next.date),"up-next-date"));
    target.append(node("span","Lunar Day "+next.lunar_day+
      (next.source==="user_supplied_month_start"?" · From supplied New Moon":" · Projected lunar month"),"up-next-meta"));
    target.onclick=()=>jumpTo(next.date);
  }
  function renderYearSummary(track){
    const box=byId("year-summary");
    box.replaceChildren();
    const lunar=monthOn(track,state.selected);
    const current=yearOn(track,state.selected);
    if(lunar&&!current){
      box.append(node("strong","Current lunar cycle"));
      box.append(node("small","New Moon "+fmt(lunar.start)));
      box.append(node("small","Next projected New Year · "+fmt(track.years[0].start_date)));
      byId("choose-year").value="current";
      return;
    }
    const record=current||track.years.find(y=>y.year===+byId("choose-year").value)||track.years[0];
    box.append(node("strong","Israelite year "+record.year));
    box.append(node("span",record.month_count+" lunar months","summary-pill"+(record.has_13th_month?" extra":"")));
    box.append(node("small","Year begins "+fmt(record.start_date)));
    if(record.thirteenth_month_start)box.append(node("small","13th month begins "+fmt(record.thirteenth_month_start)));
    box.append(node("small","Planning model · not verified crescent visibility"));
    byId("choose-year").value=String(record.year);
  }
  function renderSelectedDay(track){
    const box=byId("selected-day");box.replaceChildren();
    const d=state.selected,events=dayEvents.get(d)||[],lunar=monthOn(track,d),year=yearOn(track,d);
    box.append(node("h3",fmt(d)));
    if(lunar){
      const lunarDay=Math.round((dt(d)-dt(lunar.start))/86400000)+1;
      const label=year&&lunar.month?
        "Israelite year "+year.year+" · Month "+lunar.month+(lunar.is_thirteenth?" (13th / intercalary)":"")+" · Day "+lunarDay:
        "Lunar Day "+lunarDay+" · Month began "+fmt(lunar.start);
      box.append(node("p",label,"lunar-context"));
    }else{
      box.append(node("p","Outside the projected years available for this track; no observance has been inferred.","muted"));
    }
    const list=node("div",undefined,"day-events");
    for(const e of events){
      const card=node("article",undefined,"event type-"+e.kind);
      let badge=e.rule_status==="unapproved_draft"?"Draft feast — not approved":
                e.status==="projected"?"Projected from lunar month model":"Based on supplied month start";
      card.append(node("span",badge,"marker"),node("h4",e.title));
      card.append(node("p",(e.month?"Month "+e.month+", ":"")+"Lunar Day "+e.lunar_day+" · "+(state.track==="earlier"?"Early Start":"Late Start")));
      if(e.rule_status==="unapproved_draft"){
        card.append(node("p","Rule is a planning proposal; Shavuot and annual observance approvals remain pending."));
      }else if(e.status==="projected"){
        card.append(node("p","Computed from mean lunar months. Not an observed crescent."));
      }
      list.append(card);
    }
    if(!events.length&&lunar)box.append(node("p","No marked observance on this lunar day.","muted"));
    box.append(list);
  }
  function renderMonth(track){
    byId("month-heading").textContent=MONTHS[state.month]+" "+state.year;
    const grid=byId("month-grid");grid.replaceChildren();
    for(const day of WEEKDAYS)grid.append(node("div",day,"weekday"));
    const local=getToday(),today=iso(createDate(...local));
    for(const cell of firstDayOf(state.month,state.year)){
      const events=dayEvents.get(cell.iso)||[];
      const lunar=monthOn(track,cell.iso);
      const button=node("button",undefined,"day"+(cell.inMonth?"":" outside")+(cell.iso===state.selected?" active":"")+(cell.iso===today?" today":""));
      button.type="button";button.dataset.date=cell.iso;
      button.setAttribute("aria-pressed",String(cell.iso===state.selected));
      const label=fmt(cell.iso)+(lunar?", "+(lunar.month?"month "+lunar.month+", ":"")+"lunar day "+(Math.round((dt(cell.iso)-dt(lunar.start))/86400000)+1):"");
      button.setAttribute("aria-label",label+(events.length?", "+events.map(e=>e.title).join(", "):""));
      button.append(node("span",String(cell.day),"number"));
      if(lunar){
        const d=Math.round((dt(cell.iso)-dt(lunar.start))/86400000)+1;
        button.append(node("span",lunar.month?"M"+lunar.month+" · "+d:"Day "+d,"lunar-tag"));
      }
      if(events.length){
        const dots=node("div",undefined,"dots");
        for(const type of kinds)if(hasEvents(events,type))dots.append(node("i",undefined,"dot "+kindClass[type]));
        button.append(dots);
        const significant=events.find(e=>e.kind==="feast")||events.find(e=>e.kind==="sabbath")||events[0];
        button.append(node("span",significant.title,"event-name"));
      }
      button.onclick=()=>{
        if(!cell.inMonth){
          const d=dt(cell.iso);state.year=d.getUTCFullYear();state.month=d.getUTCMonth();
        }
        state.selected=cell.iso;draw();
      };
      grid.append(button);
    }
  }
  function draw(){
    const track=state.data.tracks[state.track];
    renderYearSummary(track);
    renderUpNext(track);
    renderMonth(track);
    renderSelectedDay(track);
    for(const b of byId("track-tabs").querySelectorAll("button")){
      b.setAttribute("aria-pressed",String(b.dataset.track===state.track));
    }
  }
  function jumpTo(date){
    const d=dt(date);state.selected=date;state.year=d.getUTCFullYear();state.month=d.getUTCMonth();draw();
  }
  function setup(data){
    if(data.schema_version!==2||!data.tracks?.earlier||!data.tracks?.later)throw Error("Unsupported two-track calendar feed");
    state.data=data;
    for(const trackId of ["earlier","later"]){
      if(!data.tracks[trackId].years?.length||!data.tracks[trackId].months?.length)throw Error("Empty lunar-year series");
    }
    const yearChoice=byId("choose-year");
    const currentOption=node("option","Current");currentOption.value="current";yearChoice.append(currentOption);
    for(const y of data.tracks.earlier.years){
      const opt=node("option",String(y.year));opt.value=String(y.year);yearChoice.append(opt);
    }
    function changeTrack(to){
      state.track=to;
      dayEvents=eventsIndex(data.tracks[to]);
      // Switching religious year starts must not drag the user to 2027.
      jumpTo(state.selected||todayIso());
    }
    for(const b of byId("track-tabs").querySelectorAll("button"))b.onclick=()=>changeTrack(b.dataset.track);
    byId("previous-month").onclick=()=>{
      const d=createDate(state.year,state.month-1,1);jumpTo(iso(d));
    };
    byId("next-month").onclick=()=>{
      const d=createDate(state.year,state.month+1,1);jumpTo(iso(d));
    };
    byId("jump-today").onclick=()=>jumpTo(iso(createDate(...getToday())));
    byId("jump-year-start").onclick=()=>{
      const track=data.tracks[state.track];
      const y=yearOn(track,state.selected)||track.years.find(x=>x.year===+yearChoice.value)||track.years[0];
      jumpTo(y.start_date);
    };
    yearChoice.onchange=()=>{
      if(yearChoice.value==="current"){jumpTo(todayIso());return}
      const year=data.tracks[state.track].years.find(y=>y.year===+yearChoice.value);
      if(year)jumpTo(year.start_date);
    };
    dayEvents=eventsIndex(data.tracks.earlier);
    // Open the actual current Gregorian month, focused on the upcoming
    // Shabbat so the user sees their next observance immediately.
    const next=nextShabbat(data.tracks.earlier);
    jumpTo(next?.date||todayIso());
  }
  fetch("calendar.json",{cache:"no-cache"}).then(r=>{
    if(!r.ok)throw Error("Calendar data not available");
    return r.json();
  }).then(setup).catch(e=>{
    byId("month-heading").textContent="Calendar unavailable";
    byId("selected-day").replaceChildren(node("p","Could not load calendar: "+e.message,"muted"));
  });
})();
