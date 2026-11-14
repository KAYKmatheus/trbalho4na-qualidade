/*
   Licensed to the Apache Software Foundation (ASF) under one or more
   contributor license agreements.  See the NOTICE file distributed with
   this work for additional information regarding copyright ownership.
   The ASF licenses this file to You under the Apache License, Version 2.0
   (the "License"); you may not use this file except in compliance with
   the License.  You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
*/
var showControllersOnly = false;
var seriesFilter = "";
var filtersOnlySampleSeries = true;

/*
 * Add header in statistics table to group metrics by category
 * format
 *
 */
function summaryTableHeader(header) {
    var newRow = header.insertRow(-1);
    newRow.className = "tablesorter-no-sort";
    var cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 1;
    cell.innerHTML = "Requests";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 3;
    cell.innerHTML = "Executions";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 7;
    cell.innerHTML = "Response Times (ms)";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 1;
    cell.innerHTML = "Throughput";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 2;
    cell.innerHTML = "Network (KB/sec)";
    newRow.appendChild(cell);
}

/*
 * Populates the table identified by id parameter with the specified data and
 * format
 *
 */
function createTable(table, info, formatter, defaultSorts, seriesIndex, headerCreator) {
    var tableRef = table[0];

    // Create header and populate it with data.titles array
    var header = tableRef.createTHead();

    // Call callback is available
    if(headerCreator) {
        headerCreator(header);
    }

    var newRow = header.insertRow(-1);
    for (var index = 0; index < info.titles.length; index++) {
        var cell = document.createElement('th');
        cell.innerHTML = info.titles[index];
        newRow.appendChild(cell);
    }

    var tBody;

    // Create overall body if defined
    if(info.overall){
        tBody = document.createElement('tbody');
        tBody.className = "tablesorter-no-sort";
        tableRef.appendChild(tBody);
        var newRow = tBody.insertRow(-1);
        var data = info.overall.data;
        for(var index=0;index < data.length; index++){
            var cell = newRow.insertCell(-1);
            cell.innerHTML = formatter ? formatter(index, data[index]): data[index];
        }
    }

    // Create regular body
    tBody = document.createElement('tbody');
    tableRef.appendChild(tBody);

    var regexp;
    if(seriesFilter) {
        regexp = new RegExp(seriesFilter, 'i');
    }
    // Populate body with data.items array
    for(var index=0; index < info.items.length; index++){
        var item = info.items[index];
        if((!regexp || filtersOnlySampleSeries && !info.supportsControllersDiscrimination || regexp.test(item.data[seriesIndex]))
                &&
                (!showControllersOnly || !info.supportsControllersDiscrimination || item.isController)){
            if(item.data.length > 0) {
                var newRow = tBody.insertRow(-1);
                for(var col=0; col < item.data.length; col++){
                    var cell = newRow.insertCell(-1);
                    cell.innerHTML = formatter ? formatter(col, item.data[col]) : item.data[col];
                }
            }
        }
    }

    // Add support of columns sort
    table.tablesorter({sortList : defaultSorts});
}

$(document).ready(function() {

    // Customize table sorter default options
    $.extend( $.tablesorter.defaults, {
        theme: 'blue',
        cssInfoBlock: "tablesorter-no-sort",
        widthFixed: true,
        widgets: ['zebra']
    });

    var data = {"OkPercent": 75.02517623363545, "KoPercent": 24.97482376636455};
    var dataset = [
        {
            "label" : "FAIL",
            "data" : data.KoPercent,
            "color" : "#FF6347"
        },
        {
            "label" : "PASS",
            "data" : data.OkPercent,
            "color" : "#9ACD32"
        }];
    $.plot($("#flot-requests-summary"), dataset, {
        series : {
            pie : {
                show : true,
                radius : 1,
                label : {
                    show : true,
                    radius : 3 / 4,
                    formatter : function(label, series) {
                        return '<div style="font-size:8pt;text-align:center;padding:2px;color:white;">'
                            + label
                            + '<br/>'
                            + Math.round10(series.percent, -2)
                            + '%</div>';
                    },
                    background : {
                        opacity : 0.5,
                        color : '#000'
                    }
                }
            }
        },
        legend : {
            show : true
        }
    });

    // Creates APDEX table
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.2497482376636455, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.08391608391608392, 500, 1500, "Login responsavel"], "isController": false}, {"data": [0.0375, 500, 1500, "Criar reserva restrita"], "isController": false}, {"data": [0.9948717948717949, 500, 1500, "Preparar intervalo unico"], "isController": false}, {"data": [0.0, 500, 1500, "Pesquisar disponibilidade"], "isController": false}, {"data": [0.025210084033613446, 500, 1500, "Aprovar reserva"], "isController": false}, {"data": [0.16923076923076924, 500, 1500, "Login solicitante"], "isController": false}]}, function(index, item){
        switch(index){
            case 0:
                item = item.toFixed(3);
                break;
            case 1:
            case 2:
                item = formatDuration(item);
                break;
        }
        return item;
    }, [[0, 0]], 3);

    // Create statistics table
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 993, 248, 24.97482376636455, 33478.54078549849, 0, 121695, 30191.0, 89987.2, 91102.9, 120274.06, 2.758593867198569, 9.802604946543562, 0.9350790899348828], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["Login responsavel", 143, 27, 18.88111888111888, 42832.013986014, 200, 90124, 59848.0, 60777.8, 89894.6, 90119.6, 0.40792108581176295, 0.11497016453054844, 0.17038405110566582], "isController": false}, {"data": ["Criar reserva restrita", 160, 62, 38.75, 42118.981250000004, 495, 120245, 33376.5, 90447.8, 90727.15, 120187.05, 0.45464749190869547, 0.16989342068248273, 0.23874543221347974], "isController": false}, {"data": ["Preparar intervalo unico", 195, 0, 0.0, 13.846153846153845, 0, 1064, 1.0, 1.0, 2.0, 802.8799999999978, 0.6548458593592585, 0.0, 0.0], "isController": false}, {"data": ["Pesquisar disponibilidade", 181, 57, 31.49171270718232, 43550.13812154696, 810, 120692, 31278.0, 92766.40000000001, 93947.2, 120556.7, 0.5057123139551453, 9.32026179343468, 0.1906189230702605], "isController": false}, {"data": ["Aprovar reserva", 119, 73, 61.34453781512605, 50216.31932773109, 830, 121695, 59900.0, 92590.0, 120275.0, 121504.4, 0.3389289844092667, 0.10510592331802932, 0.1510516945025149], "isController": false}, {"data": ["Login solicitante", 195, 29, 14.871794871794872, 33431.58461538462, 139, 89974, 32345.0, 60938.0, 84412.6, 86637.99999999997, 0.5474467923829095, 0.15660959095196786, 0.20097723639033235], "isController": false}]}, function(index, item){
        switch(index){
            // Errors pct
            case 3:
                item = item.toFixed(2) + '%';
                break;
            // Mean
            case 4:
            // Mean
            case 7:
            // Median
            case 8:
            // Percentile 1
            case 9:
            // Percentile 2
            case 10:
            // Percentile 3
            case 11:
            // Throughput
            case 12:
            // Kbytes/s
            case 13:
            // Sent Kbytes/s
                item = item.toFixed(2);
                break;
        }
        return item;
    }, [[0, 0]], 0, summaryTableHeader);

    // Create error table
    createTable($("#errorsTable"), {"supportsControllersDiscrimination": false, "titles": ["Type of error", "Number of errors", "% in errors", "% in all samples"], "items": [{"data": ["500/Internal Server Error", 159, 64.11290322580645, 16.012084592145015], "isController": false}, {"data": ["401/Unauthorized", 73, 29.43548387096774, 7.351460221550856], "isController": false}, {"data": ["404/Not Found", 16, 6.451612903225806, 1.6112789526686808], "isController": false}]}, function(index, item){
        switch(index){
            case 2:
            case 3:
                item = item.toFixed(2) + '%';
                break;
        }
        return item;
    }, [[1, 1]]);

        // Create top5 errors by sampler
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 993, 248, "500/Internal Server Error", 159, "401/Unauthorized", 73, "404/Not Found", 16, "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": ["Login responsavel", 143, 27, "500/Internal Server Error", 27, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["Criar reserva restrita", 160, 62, "500/Internal Server Error", 38, "401/Unauthorized", 24, "", "", "", "", "", ""], "isController": false}, {"data": [], "isController": false}, {"data": ["Pesquisar disponibilidade", 181, 57, "500/Internal Server Error", 32, "401/Unauthorized", 25, "", "", "", "", "", ""], "isController": false}, {"data": ["Aprovar reserva", 119, 73, "500/Internal Server Error", 33, "401/Unauthorized", 24, "404/Not Found", 16, "", "", "", ""], "isController": false}, {"data": ["Login solicitante", 195, 29, "500/Internal Server Error", 29, "", "", "", "", "", "", "", ""], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
