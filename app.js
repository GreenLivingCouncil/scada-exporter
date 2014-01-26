names = {
    "05_200.E1697": "Florence Moore Hall Complex", 
    "06_500.E1153": "Stern Kitchen", 
    "CLUSTER_1.E1018_05_430": "680 Lomita", 
    "CLUSTER_1.E1019_05_410": "Theta Delta Chi", 
    "CLUSTER_1.E1020_05_440": "Sigma Alpha Epsilon", 
    "CLUSTER_1.E1021_05_450": "1035 Campus Drive", 
    "CROTHERS.ALPHA_SIG_E1171": "Kappa Alpha Theta",
    "CROTHERS.ATO_E1173": "Delta Delta Delta", 
    "CROTHERS.BRANNER_HALL": "Branner Hall", 
    "CROTHERS.BRANNER_KITCHEN": "Branner Kitchen", 
    "CROTHERS.CROTHERS_HALL_E1157": "Crothers Hall", 
    "CROTHERS.E1148": "Wilbur Hall", 
    "CROTHERS.KIMBALL_HALL_E1404": "Kimball Hall",
    "CROTHERS.MANZ_2_E1409": "Lantana/Castano",
    "CROTHERS.MEMORIAL_HALL_E1156": "Crothers Memorial Hall",
    "CROTHERS.STERN": "Stern Hall",
    "CROTHERS.STERN_BURBANK_ZAPATA_E1152": "Burbank/Casa Zapata", 
    "CROTHERS.STERN_DONNER_SERRA_E1151": "Donner/Serra", 
    "CROTHERS.STERN_TWAINS_LARKINS_E1154": "Twain/Larkin", 
    "CROTHERS.TERRA_E1175": "Terra",
    "CROTHERS.TOYON_E1145": "Toyon Hall",
    "CROTHERS.WHITMAN_E1174": null, 
    "CROTHERS.WILBUR_HALL_KITCHEN_E1149": "Wilbur Kitchen",
    "CROTHERS.ZAP_E1172": "ZAP",
    "HaasMariposa.HILLEL_E1507": null, 
    "HaasMariposa.Lathrop_E1256": null, 
    "HaasMariposa.Mayfield_557_E1282": "Sigma Nu", 
    "ROBERT_MOORE_AREA.E1291_Xanadu_558_Mayfield": "Xanadu",
    "ROBERT_MOORE_AREA.E1292_North": "La Casa Italiana",
    "ROBERT_MOORE_AREA.E1293_South": "BOB",
    "ROBERT_MOORE_AREA.SIGMA_CHI_E1530": "Sigma Chi"
};

$(document).ready(function() {

    // TODO: Reload data every time empty data is received.
    // TODO: Use JSON response document.
    function loadData() {
        if (xmlhttp.readyState != 4 || xmlhttp.status != 200) {
            return;
        }
        var xmlDoc=xmlhttp.responseXML;
        // Fill in the last push date
        var dateString = xmlDoc.getElementsByTagName("date")[0].getAttribute("value");
        var dateElem = document.getElementById("date");
        dateElem.innerHTML = "Last Push:<br/>" + dateString;

        var buildingNodes = xmlDoc.getElementsByTagName("building");
        for (var i = 0; i < buildingNodes.length; i++) {
            // Fill in the data cells
            var dataNodes = buildingNodes[i].childNodes;
            var col = 0;
            for (var j = 0; j < dataNodes.length; j++) {
                var curDataNode = dataNodes[j];
                if (curDataNode.nodeType == 3) continue;
                var dataCell = document.getElementById(buildingNodes[i].getAttribute("name") + col.toString());
                dataCell.innerHTML = curDataNode.getAttribute("value");
                col += 1;
            }
        }
    }

    function pushData() {
        var xhr=new XMLHttpRequest();
        xhr.onreadystatechange = function(){
            if (xhr.readyState != 4 || xhr.status != 200) {
                return;
            }
            var xmlDoc = xhr.responseXML;
            var headerElem = xmlDoc.getElementsByTagName("transmission")[0];
            if (headerElem.getAttribute("success") == "true") {
                button.style.backgroundColor = "green";
                button.innerHTML = "Success!";
            } else {
                // Report error if not success.
                button.style.backgroundColor = "red";
                button.innerHTML = "Error: &quot;" + headerElem.getAttribute("e") + "&quot; Please report to Stephen.";
            }
        }
        var button = document.getElementById("pushbutton");
        button.setAttribute("onclick", "");
        button.innerHTML = "Pushing...";
        button.style.backgroundColor = "yellow";
        xhr.open("GET", "bin/pushdata.py", true);
        xhr.send();
    }

    function refresh(doReset) {
        // Send request for data again
        script_url = "bin/pulldata.py";
        if (doReset) {
            script_url = script_url + "?reset=true";
        }
        xmlhttp.open("GET", script_url, true); 
        xmlhttp.send();
    }

    function reset() {
        if (!window.confirm("Are you sure you want to reset the Last Readings with the most recent data?")) {
            return;
        }
        refresh(true);
    }


    /** Parsing the directory XML document. **/
    var xmlhttp=new XMLHttpRequest();
    xmlhttp.onreadystatechange=loadData;
    xmlhttp.open("GET","bin/pulldata.py", true);
    xmlhttp.send();


    // Build the empty data table
    for (var buildingCode in names) {
        var row = $("<tr></tr>");
        var buildingName = names[buildingCode] ? names[buildingCode] : buildingCode;
        row.append($("<td></td>").text(buildingName));
        // Create the data cells
        for (var j = 0; j < 3; j++) {
            row.append($("<td></td>").attr({
                "align": "right",
                "id": buildingCode+j.toString()
            }));
        }
        $("#datatable").append(row);
    }

});
