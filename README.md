# J.A.R.V.I.S.
An implementation of ChatGPT as a conversation agent that can actually control your home.

## Installation
For now, add this as a custom repository to HACS, reboot your machine and then add it through the gui integration config flow. The first dialog asks for your OpenAI API key (though it may not say that - I have no idea why it's just a blank box with a text input) which you can obtain from [OpenAI](https://platform.openai.com/account/api-keys), HomeAssistant long-lived access token, and HomeAssistant server URL. After that, it should work.

## How does it work?
By connecting "abilities" (as ChatGPT function calls).
The main ability is, of course, HomeAssistant integration, but it could be expanded even further.

## Limitations, caveats and warnings
1. It definitely works on various requests I've given it, but.... YMMV and I have limited time to work on this, so I make zero promises about when/if I can help you out. 
2. Your data (include a fair amount of data about entities in your home) is being pumped over the internet. I'm not worried by what is exposed (and it is over a secure connection) - if a hacker can do something useful with the entities created by home-assistant, they already have a lot of access to my home. But you should be aware and make a thoughtful decision. 
3. ChatGPT is limited to around 4k tokens (~3k words) per session. Passing all those entities and their current states chews up a fair number of tokens, depending on how much HA stuff you have. You may hit that limit after only a few requests. Shutting the chat window and refreshing your browser starts a new ssession. (there are probably smarter ways to deal with this, I might improve it later if I feel like it and have time).
4. It's slower than I'd like - not sure if there is anything I can do on my end to fix that (probably a little). 

## Developing
```
poetry install
poetry run python custom_components/jarvis/brains.py
```

## References and credits
* Starting code from [qui3xote/OpenAIConversationEnhanced](https://github.com/qui3xote/OpenAIConversationEnhanced)
* The official [openai_conversation component](https://github.com/home-assistant/core/tree/dev/homeassistant/components/openai_conversation)
* Inspired by [Linguflex](https://github.com/KoljaB/Linguflex), [onju-voice](https://github.com/justLV/onju-voice) and, of course, [J.A.R.V.I.S.](https://en.wikipedia.org/wiki/J.A.R.V.I.S.)

## TODO
* fix config flow
* allow selecting abilities on config flow
* maybe use [langchain](https://github.com/langchain-ai/langchain)
* integrate to local LLMs ([ref](https://www.reddit.com/r/homeassistant/comments/17h6zgh/comment/k6olxlu/?utm_source=share&utm_medium=web2x&context=3))
* calendar (Google/HA)
* reminders (does HA have them?)
* audio warning to speakers
* control music
* ifood?
    * https://gist.github.com/donkawechico/30399f34fa88f0c560f9eb0c756d2efa
    * https://community.home-assistant.io/t/fetching-a-token-every-hour/167434/8
* plex? (+sonarr/radarr)
