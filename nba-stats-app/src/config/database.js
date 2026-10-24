import { Sequelize } from "sequelize";

export const sequelize = new Sequelize("nba_stats", "root", "root", {
  host: "localhost",
  dialect: "mysql"
});