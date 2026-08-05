# AI Services Setup Guide

This guide will help you configure the AI services for virtual try-on and talking avatar generation.

## Current Configuration

- **Virtual Try-On**: Miragic API
- **Talking Avatar**: D-ID

## Step 1: Get API Keys

### Miragic API Key

1. Go to https://miragic.ai/ (or https://backend.miragic.ai/)
2. Sign up / log in to the dashboard
3. Generate an API key (used via the `X-API-Key` header)
4. Copy the key (format: `sk_live_...`)

### D-ID API Key

1. Go to https://studio.d-id.com/
2. Sign up or log in
3. Go to API section or Account Settings
4. Create an API key
5. Copy the key (format: `email:api_key`)

## Step 2: Configure Environment Variables

1. Copy the example env file:
   ```bash
   cd backend
   cp env.example .env
   ```

### (Optional) Hugging Face API Token

Keep this handy if you want to fall back to Hugging Face VTON or use other models.

## Step 2: Configure Environment Variables

1. Copy the example env file:
   ```bash
   cd backend
   cp env.example .env
   ```

2. Edit `.env` and add your API keys:
   ```env
   MIRAGIC_API_KEY=sk_live_your_key_here
   DID_API_KEY=your_email:your_api_key_here
   # Optional overrides
   # MIRAGIC_GARMENT_TYPE=full_body
   # HUGGINGFACE_API_TOKEN=hf_optional_fallback
   
   VIRTUAL_TRYON_SERVICE=miragic
   TALKING_AVATAR_SERVICE=did
   ```

3. **IMPORTANT**: Never commit your `.env` file to git! It contains sensitive API keys.

## Step 3: Test the Setup

1. Start the backend server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

2. Try uploading files through the frontend
3. Check the console logs for any API errors

## Troubleshooting

### Miragic Issues

- **Authentication**: Ensure `MIRAGIC_API_KEY` is set and mapped to the `X-API-Key` header (handled automatically by the code).
- **Garment Type**: Set `MIRAGIC_GARMENT_TYPE` to `upper_body`, `lower_body`, or `full_body` depending on the clothing you upload.
- **Polling Timeout**: Increase `MIRAGIC_POLL_TIMEOUT_SECONDS` if jobs regularly exceed 10 minutes.
- **Rate Limits**: Respect Miragic's 60 requests/minute limit; the code already polls with exponential backoff.

### D-ID Issues

- **Authentication**: Make sure your API key format is correct: `email:api_key`
- **Image Format**: D-ID works best with JPEG images. PNG is also supported.
- **Audio Format**: MP3, WAV, and other common formats are supported.
- **Processing Time**: Video generation can take 1-5 minutes depending on length.

## Alternative Services

If you want to switch services, update the `.env` file:

```env
# For Replicate (easier setup)
VIRTUAL_TRYON_SERVICE=replicate
TALKING_AVATAR_SERVICE=replicate
REPLICATE_API_TOKEN=your_token_here
MIRAGIC_API_KEY=

# For HeyGen
TALKING_AVATAR_SERVICE=heygen
HEYGEN_API_KEY=your_key_here

# For Hugging Face try-on (fallback)
VIRTUAL_TRYON_SERVICE=huggingface
HUGGINGFACE_API_TOKEN=hf_your_token_here
```

## API Costs

- **Miragic**: Usage-based pricing (see Miragic dashboard)
- **Hugging Face**: Free tier available, pay-per-use for inference
- **D-ID**: Free tier with limited credits, then pay-per-video
- Check each service's pricing page for current rates

