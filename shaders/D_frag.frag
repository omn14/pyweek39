#version 330

uniform vec2 iResolution;
uniform sampler2D iChannel0;

uniform sampler2D iChannel2;
//uniform float iTimeDelta;
in vec2 uv;
out vec4 fragColor;

// Subtract pressure gradient to ensure zero divergence.

#define PressureTexture iChannel2
#define VelocityTexture iChannel0

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    vec2 inverseResolution = vec2(1.0) / iResolution.xy;
    //vec2 uv = fragCoord.xy * inverseResolution;
    
    float x0 = texture(PressureTexture, uv - vec2(inverseResolution.x, 0)).x;
    float x1 = texture(PressureTexture, uv + vec2(inverseResolution.x, 0)).x;
    float y0 = texture(PressureTexture, uv - vec2(0, inverseResolution.y)).x;
    float y1 = texture(PressureTexture, uv + vec2(0, inverseResolution.y)).x;
    vec2 pressureGradient = (vec2(x1, y1) - vec2(x0, y0)) * 0.5;
    vec2 oldV = texture(VelocityTexture, uv).xy;
    
    fragColor = vec4(oldV - pressureGradient, 0.0, 0.0);
}

void main()
{
    mainImage(fragColor, uv);
}