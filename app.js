$(document).ready(function() {

    function escapeId(myid) {
        return "#" + myid.replace( /(:|\.|\[|\])/g, "\\$1" );
    }

    function loadData(event) {
        if (event.data.doReset) {
            if (!window.confirm("Are you sure you want to reset the Last Readings with the most recent data?")) {
                return;
            }
        }

        $.getJSON( "bin/pulldata.py" + (event.data.doReset ? "?reset=true" : ""))
        .done(function( data ) {
            // Update timestamps
            $("#pull-date").text(data.current_date);
            $("#push-date").text(data.last_push_date);
            
            var readings = data.readings;
            for (var building in readings) {
                if (readings.hasOwnProperty(building)) {
                    var row = readings[building];
                    for (var column in row) {
                        if (row.hasOwnProperty(column)) {
                            $(escapeId(building + column)).text(row[column]);
                        }
                    }
                }
            }
        })
        .fail(function( jqxhr, textStatus, error ) {
            var err = textStatus + ", " + error;
            // TODO: Reload data every time empty data is received.
            // TODO display visible error message
            console.log( "Request Failed: " + err );
        });
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

    // Bind handlers for buttons.
    $(window).on("tableCreated", {"doReset": false}, loadData);
    $("#refreshButton").click({"doReset": false}, loadData);
    $("#resetButton").click({"doReset": true}, loadData);
    $("#pushButton").click(pushData);

    // Build the empty data table
    $.getJSON("names.json")
    .done(function( names ) {
        var columnNames = ["last_reading", "new_reading", "difference"];

        for (var buildingCode in names) {
            var row = $("<tr></tr>");
            var buildingName = names[buildingCode] ? names[buildingCode] : buildingCode;
            row.append($("<td></td>").text(buildingName));
            for (var j = 0; j < 3; j++) {
                row.append($("<td></td>").attr({
                    "align": "right",
                    "id": buildingCode + columnNames[j]
                }));
            }
            $("#datatable").append(row);
        }
        
        $("#maintable").fadeIn("slow");
        $(window).trigger("tableCreated");
    })
    .fail(function( jqxhr, textStatus, error ) {
        var err = textStatus + ", " + error;
        // TODO display visible error message
        console.log( "Request Failed: " + err );
    });

});
