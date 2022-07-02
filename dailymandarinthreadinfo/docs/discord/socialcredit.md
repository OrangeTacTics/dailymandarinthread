# Social Credit
To ensure social harmony, everyone on the Daily Mandarin Thread has a Social Credit Score. It appears as part of your nickname in the server.

Social credit is obtained through positive interactions with the server. Social credit is lost through negative interactions. The easiest way to start building your social credit is to play nice on the server. When other users react to your posts, your social credit builds.

Ultimately, social credit is at the discretion of the Party.

<div id="leaderboard"></div>

<script type="text/javascript">

var leaderboardDiv = document.getElementById("leaderboard");

fetch('/leaderboard').then(function(response) {
    response.json().then(function(json_data) {
        var leaderboard = json_data['leaderboard'];
        for (var i = 0; i < leaderboard.length; i++) {
            console.log(leaderboard[i]['name']);
            console.log(leaderboard[i]['credit']);
            leaderboardDiv.innerHTML += leaderboard[i]['name'] + ' ' + leaderboard[i]['credit'];
        }
    });
});
</script>
