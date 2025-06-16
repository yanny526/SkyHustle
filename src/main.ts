import { Telegraf } from 'telegraf';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

const bot = new Telegraf(process.env.BOT_TOKEN || '');

// Basic command handler
bot.command('start', (ctx) => {
    ctx.reply('Welcome to SkyHustle Bot! 🚀');
});

// Launch bot
async function main() {
    try {
        console.log('Starting bot...');
        await bot.launch();
        console.log('Bot is running!');
    } catch (error) {
        console.error('Error starting bot:', error);
        process.exit(1);
    }
}

// Enable graceful stop
process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));

main(); 