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
        var text = mainDoc.body ? mainDoc.body.innerText : '';
        return text;
    } catch(e) { return 'ERROR: ' + e.message; }
};
