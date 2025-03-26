#version 330

uniform vec2 iResolution;
uniform sampler2D iChannel0;
//uniform float iTimeDelta;
in vec2 uv;
out vec4 fragColor;

// Compute divergence.

#define VelocityTexture iChannel0

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    vec2 inverseResolution = vec2(1.0) / iResolution.xy;
    //vec2 uv = fragCoord.xy * inverseResolution;
    
    // Obstacle?
    if(texture(VelocityTexture, uv).z > 0.0)
    {
        fragColor = vec4(0.0);
        return;
    }

    float x0 = texture(VelocityTexture, uv - vec2(inverseResolution.x, 0)).x;
    float x1 = texture(VelocityTexture, uv + vec2(inverseResolution.x, 0)).x;
    float y0 = texture(VelocityTexture, uv - vec2(0, inverseResolution.y)).y;
    float y1 = texture(VelocityTexture, uv + vec2(0, inverseResolution.y)).y;
    float divergence = ((x1-x0) + (y1-y0)) * 0.5;
    fragColor = vec4(divergence);
/* 
    // Encoding
    float value = divergence; // Sample negative value
    float absValue = abs(value);
    bool isNegative = value < 0.0;
    vec4 encoded = vec4(
                    absValue,           // Red: magnitude
                    isNegative ? 1.0 : 0.0,  // Green: sign flag
                    0.0, 1.0);          // Blue: unused, Alpha: unused
    fragColor = vec4(encoded);
 */
}

void main()
{
    mainImage(fragColor, uv);
}