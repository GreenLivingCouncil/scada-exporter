$(document).ready(function() {

    function escapeId(myid) {
        return "#" + myid.replace( /(:|\.|\[|\])/g, "\\$1" );
    }

    function handleFetchFail(jqxhr, textStatus, error) {
        var err = textStatus + ", " + error;
        // TODO display visible error message
        console.log( "Request Failed: " + err );
    }

    function loadData(event) {
        if (event.data.doReset
            && !window.confirm("Are you sure you want to reset the Last Readings with the most recent data?")) {
            return;
        }

        $.getJSON( "bin/pulldata.py" + (event.data.doReset ? "?reset=true" : ""))
        .fail(handleFetchFail)
        .done(function( data ) {
            // TODO: Reload data every time empty data is received.
            
            // Update timestamps
            $("#pull-date").text(data.current_date);
            $("#push-date").text(data.last_push_date);
            
            var readings = data.readings;
            for (var building in readings) {
                if (readings.hasOwnProperty(building)) {
                    var row = readings[building];
                    if (row.error) {
                        $(escapeId(building + "error")).text(row.error).parent().show();
                        continue;
                    }
                    for (var column in row) {
                        if (row.hasOwnProperty(column)) {
                            $(escapeId(building + column)).text(row[column]);
                        }
                    }
                }
            }
        });
    }

    function pushData() {
        $.getJSON("bin/pushdata.py")
        .fail(handleFetchFail)
        .done(function( response ) {
            if (response.success) {
                $("#pushButton").css("background-color", "green")
                                .text("Success!");
            } else {
                $("#pushButton").css("background-color", "red")
                                .text("Error: Please report to Stephen.");
                console.log(response.error);
            }
        });

        $("#pushButton").css("background-color", "yellow")
                        .text("Pushing...");
    }

    /* Build the empty data table. */
    function createTable() {
        $.getJSON("names.json")
        .fail(handleFetchFail)
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
                var errorRow = $("<tr></tr>")
                    .append( $("<td></td>").attr({"colspan": 4, "id": buildingCode + "error", "class": "meter-error"}) )
                    .hide();
                $("#datatable").append(row);
                $("#datatable").append(errorRow);
            }
            
            $("#maintable").fadeIn("slow");
            $(window).trigger("tableCreated");
        });
    }

    // Bind handlers for buttons.
    $(window).on("tableCreated", {"doReset": false}, loadData);
    $("#refreshButton").click({"doReset": false}, loadData);
    $("#resetButton").click({"doReset": true}, loadData);
    $("#pushButton").click(pushData);

    createTable();


});
