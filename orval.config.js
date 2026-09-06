export default {
  socialGame: {
    input: {
      target: process.env.ORVAL_OPENAPI_TARGET || "http://127.0.0.1:8000/openapi.json",
    },
    output: {
      target: "./engine/web/react/api/generated/index.ts",
      client: "react-query",
      mode: "tags-split",
      schemas: "./engine/web/react/api/generated/model",
      clean: true,
      prettier: false,
      override: {
        mutator: {
          path: "./engine/web/react/api/orval-mutator.ts",
          name: "orvalFetch",
        },
        operations: {
          chatStreamApiChatStreamPost: {
            mutator: {
              path: "./engine/web/react/api/orval-mutator.ts",
              name: "orvalFetchStream",
            },
          },
        },
      },
    },
  },
}
