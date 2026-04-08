window._queryEMR = function(chartNo) {
    var topDoc = window.frames['topFrame'].document;
    topDoc.getElementById('txtChartNo').value = chartNo;
    topDoc.getElementById('BTQuery').click();
};
window._getPatientName = function() {
    try {
        var topDoc = window.frames['topFrame'].document;
        var el = topDoc.getElementById('lblName');
        return el ? el.innerText.trim() : '';
    } catch(e) { return ''; }
};
window._clickDoctorVisit = function(doctorName) {
    var leftDoc = window.frames['leftFrame'].document;
    var links = leftDoc.querySelectorAll('a');
    var matches = [];
    for (var i = 0; i < links.length; i++) {
        var t = links[i].innerText.trim();
        if (t.indexOf('\u9580\u8a3a') >= 0 && t.indexOf(doctorName) >= 0) {
            var m = t.match(/([0-9]{4}\/[0-9]{2}\/[0-9]{2})/);
            var d = m ? m[1] : '0000/00/00';
            matches.push({el: links[i], text: t, date: d});
        }
    }
    if (matches.length === 0) return null;
    matches.sort(function(a,b){ return b.date.localeCompare(a.date); });
    matches[0].el.click();
    return matches[0].text;
};
window._listVisits = function() {
    var leftDoc = window.frames['leftFrame'].document;
    var links = leftDoc.querySelectorAll('a');
    var v = [];
    for (var i = 0; i < links.length; i++) {
        var t = links[i].innerText.trim();
        if (t.indexOf('\u9580\u8a3a') >= 0 || t.match(/[0-9]{4}\/[0-9]{2}\/[0-9]{2}/)) v.push(t);
    }
    return v;
};
window._extractEMR = function() {
    try {
        var mainDoc = window.frames['mainFrame'].document;
        // Only extract div.small containing SOAP sections
        // Skip: div.medicine, div.plan, div.iportlet-content
        var divs = mainDoc.querySelectorAll('div.small');
        var texts = [];
        for (var i = 0; i < divs.length; i++) {
            var parent = divs[i].parentElement;
            // Skip if parent is iportlet-content (medicine/plan blocks)
            if (parent && parent.className && (
                parent.className.indexOf('iportlet-content') >= 0 ||
                parent.className.indexOf('medicine') >= 0 ||
                parent.className.indexOf('plan') >= 0)) {
                continue;
            }
            var t = divs[i].innerText.trim();
            if (t && (t.indexOf('[Diagnosis]') >= 0 || t.indexOf('[Subjective]') >= 0 ||
                t.indexOf('[Objective]') >= 0 || t.indexOf('[Assessment') >= 0)) {
                texts.push(t);
            }
        }
        if (texts.length > 0) return texts.join('\n');
        // Fallback: if no div.small with SOAP found, try getting text
        // but still exclude medicine/plan blocks
        var allDivs = mainDoc.querySelectorAll('div');
        var fallback = [];
        for (var j = 0; j < allDivs.length; j++) {
            var cls = allDivs[j].className || '';
            if (cls.indexOf('medicine') >= 0 || cls.indexOf('plan') >= 0 ||
                cls.indexOf('iportlet') >= 0) continue;
            var txt = allDivs[j].innerText.trim();
            if (txt && (txt.indexOf('[Diagnosis]') >= 0 || txt.indexOf('[Subjective]') >= 0 ||
                txt.indexOf('[Objective]') >= 0 || txt.indexOf('[Assessment') >= 0)) {
                fallback.push(txt);
                break;  // take first match to avoid duplicates
            }
        }
        if (fallback.length > 0) return fallback[0];
        return mainDoc.body ? mainDoc.body.innerText : '';
    } catch(e) { return 'ERROR: ' + e.message; }
};
