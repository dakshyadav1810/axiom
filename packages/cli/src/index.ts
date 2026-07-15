#!/usr/bin/env node
import { Command } from "commander";
import { registerCommands } from "./commands.js";

const program = new Command("axiom").description(
  "Axiom — deterministic-first AI-native testing platform",
);
registerCommands(program);
program.parseAsync(process.argv);
