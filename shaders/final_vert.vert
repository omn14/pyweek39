#version 330

// Input attributes from the vertex data
in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;

// Output variables to the fragment shader
out vec2 uv;

uniform mat4 p3d_ModelViewProjectionMatrix;

void main() {
    // Pass the texture coordinates to the fragment shader
    uv = p3d_MultiTexCoord0;

    // Transform the vertex position
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
}
