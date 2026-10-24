import { getGames, getPlayersByTeam } from "../services/nbaService.js";

// jogos
export const getGamesController = async (req, res) => {
  try {
    const games = await getGames();
    res.json(games);
  } catch (error) {
    console.error(error.message);
    res.status(500).json({ error: error.message });
  }
};

// jogadores
export const getPlayersController = async (req, res) => {
  try {
    const { teamId } = req.params;

    const players = await getPlayersByTeam(teamId);

    res.json(players);
  } catch (error) {
    console.error(error.message);
    res.status(500).json({ error: error.message });
  }
};