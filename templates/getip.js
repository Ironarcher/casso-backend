$.getJSON('//api.ipify.org?format=jsonp&callback=?', function(data) {
	$("#ip").html("IP: " + data.ip);
});