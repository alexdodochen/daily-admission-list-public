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
        // Collect: section headers (<p> with [Diagnosis] etc.) + all div.small
        // Exclude: div.medicine, div.plan inside div.iportlet-content
        var result = [];

        // Get all div.small that are NOT inside medicine/iportlet-content
        var divs = mainDoc.querySelectorAll('div.small');
        for (var i = 0; i < divs.length; i++) {
            // Walk up parents to check if inside excluded containers
            var skip = false;
            var node = divs[i].parentElement;
            while (node && node !== mainDoc.body) {
                var cls = node.className || '';
                if (cls.indexOf('medicine') >= 0 ||
                    cls.indexOf('iportlet-content') >= 0) {
                    skip = true;
                    break;
                }
                node = node.parentElement;
            }
            if (!skip) {
                result.push(divs[i].innerText.trim());
            }
        }

        // Also get section header <p> tags ([Diagnosis], [Subjective], etc.)
        var ps = mainDoc.querySelectorAll('p');
        var headers = {};
        for (var j = 0; j < ps.length; j++) {
            var pt = ps[j].innerText.trim();
            if (pt.indexOf('[Diagnosis]') >= 0 || pt.indexOf('[Subjective]') >= 0 ||
                pt.indexOf('[Objective]') >= 0 || pt.indexOf('[Assessment') >= 0) {
                headers[pt] = true;
            }
        }

        // Interleave: headers are placed before their corresponding div.small
        // Since div.small blocks are in reverse order in DOM (Assessment->Obj->Subj->Diag),
        // but innerText from body would give correct order, just combine all div.small texts
        // The section labels are embedded in the p tags between div.small blocks
        if (result.length > 0) {
            // Reconstruct with section headers by scanning body children in order
            var ordered = [];
            var children = mainDoc.body.children;
            for (var k = 0; k < children.length; k++) {
                var el = children[k];
                var cls2 = el.className || '';
                // Skip excluded blocks
                if (cls2.indexOf('medicine') >= 0 || cls2.indexOf('iportlet') >= 0) continue;
                var txt = el.innerText.trim();
                if (!txt) continue;
                // Section headers
                if (el.tagName === 'P' && headers[txt]) {
                    ordered.push(txt);
                }
                // div.small content
                if (el.tagName === 'DIV' && cls2.indexOf('small') >= 0) {
                    ordered.push(txt);
                }
            }
            if (ordered.length > 0) return ordered.join('\n');
            return result.join('\n');
        }

        // Fallback
        return mainDoc.body ? mainDoc.body.innerText : '';
    } catch(e) { return 'ERROR: ' + e.message; }
};
