import express from "express";
import { getGamesController, getPlayersController } from "../controllers/gameController.js";

const router = express.Router();

router.get("/games", getGamesController);
router.get("/team/:teamId", getPlayersController);

export default router;