import { DataTypes } from "sequelize";
import { sequelize } from "../config/database.js";

export const Player = sequelize.define("Player", {
  name: DataTypes.STRING,
  team: DataTypes.STRING,
  points: DataTypes.FLOAT,
  assists: DataTypes.FLOAT,
  rebounds: DataTypes.FLOAT
});