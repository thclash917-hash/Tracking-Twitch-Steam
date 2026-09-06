// Exemple de fonction Serverless Node.js (Vercel / Netlify)
export default async function handler(req, res) {
    const CLIENT_ID = process.env.TWITCH_CLIENT_ID;
    const CLIENT_SECRET = process.env.TWITCH_CLIENT_SECRET;

    try {
        // 1. Obtenir le token d'accès Twitch de manière sécurisée
        const tokenRes = await fetch(`https://id.twitch.tv/oauth2/token?client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}&grant_type=client_credentials`, {
            method: 'POST'
        });
        const tokenData = await tokenRes.json();
        const accessToken = tokenData.access_token;

        // 2. Récupérer les top streams / jeux de Twitch
        const gamesRes = await fetch('https://api.twitch.tv/helix/games/top?first=100', {
            headers: {
                'Client-ID': CLIENT_ID,
                'Authorization': `Bearer ${accessToken}`
            }
        });
        const gamesData = await gamesRes.json();

        // 3. Renvoyer les données au frontend de votre site
        res.status(200).json(gamesData.data);
    } catch (error) {
        res.status(500).json({ error: "Erreur lors de la récupération des données Twitch" });
    }
}
