#!/bin/bash
ssh brick "cd /DATA/AppData/homeassistant/custom_components/jarvis/server; git pull; docker restart jarvis"
