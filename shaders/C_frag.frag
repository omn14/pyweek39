#version 330

uniform vec2 iResolution;
uniform sampler2D iChannel0;
uniform sampler2D iChannel1;
uniform sampler2D iChannel2;
//uniform float iTimeDelta;
uniform vec2 iMousePos;
#define MAX_LOGS 200
uniform int array_length;
uniform vec2 iLogPos[MAX_LOGS];
uniform float iLogVelocities[MAX_LOGS];
in vec2 uv;
out vec4 gl_FragColor;

// Jacobi iteration
// For a more accurate result, this should be executed multiple times.

#define DivergenceTexture iChannel1
#define PressureTexture iChannel2
#define VelocityTexture iChannel0

//vec2 inverseResolution;
vec2 border;
//vec2 uv;
vec2 inverseResolution = vec2(1.0) / iResolution.xy;
const float BarrierRadiusSq = 0.001;

float samplePressure(vec2 pos)
{
    // Obstacle?
    if(texture(VelocityTexture, pos).z > 0.0)
    {
        return 0.0;
    }

    //mouse
    vec2 toBarrier = iMousePos - uv;
    toBarrier.x *= inverseResolution.y / inverseResolution.x;
    //vec4 fragColorN = vec4(0.0);
    if(dot(toBarrier, toBarrier) < BarrierRadiusSq)
    {
        //fragColor = vec4(0.0, 0.0, 999.0, 0.0);
        //fragColor = vec4(outputVelocity+0.1, 0.0, 0.0);
        return texture(PressureTexture, pos).x+0.9;
    }

    for (int i = 0; i < MAX_LOGS; i++) {
        //BarrierPosition = vec2(1.2, abs(sin(iTime))/2);
        //BarrierPosition = iLogPos;
        if (i >= array_length) break;
        toBarrier = iLogPos[i] - uv;
        toBarrier.x *= inverseResolution.y / inverseResolution.x;
        //vec4 fragColorN = vec4(0.0);
        if(dot(toBarrier, toBarrier) < BarrierRadiusSq)
        {
            //fragColor = vec4(0.0, 0.0, 999.0, 0.0);
            //fragColor = vec4(outputVelocity+0.1, 0.0, 0.0);
            return texture(PressureTexture, pos).x+0.2*iLogVelocities[i];
        }
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
    //inverseResolution = vec2(1.0) / iResolution.xy;
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