#!/bin/bash
rm -f /tmp/*.png /tmp/*.jpg /tmp/*.jpeg /tmp/*.suf /tmp/*.gif /tmp/*.webp /tmp/*.silk /tmp/*.pcm
LD_PRELOAD=/lib64/libjemalloc.so.2 /root/.sdkman/candidates/java/current/bin/java \
	-Djava.util.logging.config.file=logging.properties \
	-Dlog4j.logger.marytts=WARN \
	--enable-native-access=ALL-UNNAMED \
	--sun-misc-unsafe-memory-access=allow \
	-Xms512m -Xmx1536m \
	-XX:MaxHeapFreeRatio=40 \
	-jar KarenBot-9.1.jar
