# J.A.R.V.I.S.
An implementation of ChatGPT as a conversation agent that can actually control your home.

## Installation
For now, add this as a custom repository to HACS, reboot your instance and then add it through the GUI integration config flow.

Currently, J.A.R.V.I.S. only works with OpenAI's ChatGPT, so their key is required. Both Home Assistant and Google configuration are optional, provide them if you want to enable those abilities. Without any ability configured, J.A.R.V.I.S. will still answer questions as if it was ChatGPT.

Then, go to [Voice assistants](http://127.0.0.1:8123/config/voice-assistants/assistants), create a new assistant and change the "Conversation agent" to "J.A.R.V.I.S."

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
poetry run python langbrain.py
```

## Abilities
### Matrix
```
poetry run matrix-commander --credentials "$PWD/jarvis-config/credentials.json" --store "$PWD/jarvis-config/store" --login password
# If using Beeper, verify this device on Element/Riot
poetry run matrix-commander --credentials "$PWD/jarvis-config/credentials.json" --store "$PWD/jarvis-config/store" --verify
```

## References and credits
* Starting code from [qui3xote/OpenAIConversationEnhanced](https://github.com/qui3xote/OpenAIConversationEnhanced)
* The official [openai_conversation component](https://github.com/home-assistant/core/tree/dev/homeassistant/components/openai_conversation)
* Inspired by [Linguflex](https://github.com/KoljaB/Linguflex), [onju-voice](https://github.com/justLV/onju-voice) and, of course, [J.A.R.V.I.S.](https://en.wikipedia.org/wiki/J.A.R.V.I.S.)

## TODO
* fix config flow
* allow selecting abilities on config flow
* integrate to local LLMs ([ref](https://www.reddit.com/r/homeassistant/comments/17h6zgh/comment/k6olxlu/?utm_source=share&utm_medium=web2x&context=3))
* control music
* ifood?
    * https://gist.github.com/donkawechico/30399f34fa88f0c560f9eb0c756d2efa
    * https://community.home-assistant.io/t/fetching-a-token-every-hour/167434/8
* plex? (+sonarr/radarr)
* checkpointer on graph
