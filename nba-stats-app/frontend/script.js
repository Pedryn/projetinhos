const gamesDiv = document.getElementById("games");

fetch("http://localhost:3000/games")
  .then(res => res.json())
  .then(games => {
    games.forEach(game => {
      const div = document.createElement("div");

      div.innerHTML = `
        <h3>
          ${game.home_team.full_name} vs ${game.visitor_team.full_name}
        </h3>

        <button onclick="goToGame(${game.home_team.id}, ${game.visitor_team.id})">
          Ver jogadores
        </button>
      `;

      gamesDiv.appendChild(div);
    });
  });

function goToGame(homeId, awayId) {
  window.location.href = `game.html?home=${homeId}&away=${awayId}`;
}