#version 330

uniform vec2 iResolution;
uniform sampler2D iChannel0;
uniform sampler2D iChannel1;
uniform sampler2D iChannel2;
//uniform float iTimeDelta;
in vec2 uv;
out vec4 gl_FragColor;

// Jacobi iteration
// For a more accurate result, this should be executed multiple times.

#define DivergenceTexture iChannel1
#define PressureTexture iChannel2
#define VelocityTexture iChannel0

vec2 inverseResolution;
vec2 border;
//vec2 uv;

float samplePressure(vec2 pos)
{
    // Obstacle?
    if(texture(VelocityTexture, pos).z > 0.0)
    {
        return 0.0;
    }
    
    // Boundary condition: Vanish for at walls.
    if(pos.x > 1.0 - border.x || pos.y > 1.0 - border.y ||
      	pos.x < border.x || pos.y < border.y)
    {
        return 0.0;
    }
   	else
    {
    	return texture(PressureTexture, pos).x;
    }
}

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    inverseResolution = vec2(1.0) / iResolution.xy;
    border = inverseResolution * 2.0;
    //uv = fragCoord.xy * inverseResolution;
    
    float div = texture(DivergenceTexture, uv).x;
    /* vec4 divenc = texture(DivergenceTexture, uv);
    // Decoding
    float magnitude = divenc.r;
    bool isNegative = divenc.g > 0.5;
    float div = isNegative ? -magnitude : magnitude;
 */
    float x0 = samplePressure(uv - vec2(inverseResolution.x, 0));
    float x1 = samplePressure(uv + vec2(inverseResolution.x, 0));
    float y0 = samplePressure(uv - vec2(0, inverseResolution.y));
    float y1 = samplePressure(uv + vec2(0, inverseResolution.y));
    
   	fragColor = vec4((x0 + x1 + y0 + y1 - div) * 0.25);
}

void main()
{
    mainImage(gl_FragColor, uv);
}