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
        $.getJSON("bin/pushdata.py")
        .done(function( response ) {
            if (response.success) {
                $("#pushButton").css("background-color", "green")
                                .text("Success!");
            } else {
                $("#pushButton").css("background-color", "red")
                                .text("Error: Please report to Stephen.");
                console.log(response.error);
            }
        })
        .fail(function( jqxhr, textStatus, error ) {
            var err = textStatus + ", " + error;
            // TODO display visible error message
            console.log( "Request Failed: " + err );
        });

        $("#pushButton").css("background-color", "yellow")
                        .text("Pushing...");
    }

    /* Build the empty data table. */
    function createTable() {
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
    }

    // Bind handlers for buttons.
    $(window).on("tableCreated", {"doReset": false}, loadData);
    $("#refreshButton").click({"doReset": false}, loadData);
    $("#resetButton").click({"doReset": true}, loadData);
    $("#pushButton").click(pushData);

    createTable();


});
