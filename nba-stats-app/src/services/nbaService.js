import axios from "axios";
import dotenv from "dotenv";

dotenv.config();

// 🔥 JOGOS (balldontlie)
export async function getGames() {
  const today = new Date();
  const tomorrow = new Date();
  tomorrow.setDate(today.getDate() + 1);

  const format = d => d.toISOString().split("T")[0];

  const response = await axios.get(
    "https://api.balldontlie.io/v1/games",
    {
      headers: {
        Authorization: process.env.API_KEY
      },
      params: {
        dates: [format(today), format(tomorrow)],
        per_page: 20
      }
    }
  );

  return response.data.data;
}

// 🔥 JOGADORES (NBA oficial)

export async function getPlayersByTeam(teamId) {
  const url = "https://stats.nba.com/stats/commonteamroster";

  const response = await axios.get(
    `https://api.allorigins.win/raw?url=${encodeURIComponent(
      `${url}?TeamID=${teamId}&Season=2023-24`
    )}`
  );

  const players = response.data.resultSets[0].rowSet;

  return players.map(p => ({
    name: p[3],
    number: p[4],
    position: p[5]
  }));
}