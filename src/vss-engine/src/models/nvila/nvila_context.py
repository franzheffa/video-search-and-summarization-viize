######################################################################################################
# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
######################################################################################################


from .nvila_model import NVila


class NVilaContext:
    """NVILA VLM Model Conversation context.

    This helps maintain conversation context for different chunks/files while
    not having to reload the actual model."""

    def __init__(self, model: NVila) -> None:
        """NVilaContext constructor

        Args:
            model: NVilaModel instance
        """
        # Get the conversation object
        self._model = model

    def set_video_embeds(self, chunks, video_embeds, video_frames, video_frames_times):
        """Set the chunks, and corresponding video embeddings and frame times.
        Accepts batched inputs (lists)"""
        self._video_frames_times = video_frames_times
        self._chunks = chunks

        self._video_frames = video_frames

    def ask(self, query, respond=True, skip_time_tokens=False, generation_config=None, chunk=None):
        """Ask a query to the model

        Args:
            query: Prompt for the VLM model
            respond: If true, generate response. If false, only add to the conversation context.
                     Defaults to True.
            skip_time_tokens: Skip decoding time tokens in the response. Defaults to False.
            generation_config: Dictionary of VLM output parameters (top-k, seed etc).
                               Defaults to None.

        Returns:
            List of VLM responses per chunk for the batched input
        """
        if self._model.num_time_tokens == 0:
            string_of_times = ""
            for t, frame_time in enumerate(self._video_frames_times[0]):
                string_of_times += (
                    f"<T{t}>"
                    if self._chunks[0].file.startswith("rtsp://")
                    else self._chunks[0].get_timestamp(frame_time)
                )
                string_of_times += " "
            query = (
                "These are frames sampled from the same video at times "
                + string_of_times
                + ". "
                + query
            )

        if not respond:
            # Only for adding the prompt to the context. No need for VLM response
            return

        # Generate a response from the VLM model
        return self._model.generate(
            query,
            self._video_frames[0],
            generation_config,
            [
                self._chunks[0].get_timestamp(frame_time)
                for frame_time in self._video_frames_times[0]
            ],
        )
