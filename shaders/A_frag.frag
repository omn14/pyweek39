#version 330

uniform vec2 iResolution;
uniform sampler2D iChannel3;
uniform float iTimeDelta;
uniform float iTime;
in vec2 uv;
out vec4 gl_FragColor;

// Advection & force

// Magic force within a rectangle.
const vec2 Force = vec2(100.0, 0.0);
const vec2 ForceAreaMin = vec2(0.0, 0.2); 
const vec2 ForceAreaMax = vec2(0.06, 0.8);

// Circular barrier.
vec2 BarrierPosition = vec2(0.2, 0.5);
const float BarrierRadiusSq = 0.01;

#define VelocityTexture iChannel3



void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    
    vec2 inverseResolution = vec2(1.0) / iResolution.xy;
    //vec2 uv = fragCoord.xy * inverseResolution;

    

    // Simple advection by backstep.
    // Todo: Try better methods like MacCormack (http://http.developer.nvidia.com/GPUGems3/gpugems3_ch30.html)
    vec2 oldVelocity = texture(VelocityTexture, uv).xy;
    vec2 samplePos = uv - oldVelocity * iTimeDelta * inverseResolution;
    //samplePos = uv - oldVelocity * iTimeDelta;
    //samplePos = uv - oldVelocity;
    //samplePos = uv - oldVelocity * iTimeDelta;
    //samplePos = uv - oldVelocity * inverseResolution-vec2(inverseResolution.x,0);
    //samplePos = uv - inverseResolution;
    vec2 outputVelocity = texture(VelocityTexture, samplePos).xy;
    //vec2 outputVelocity = texture(VelocityTexture, vec2(uv.x-0.1*iTimeDelta,0)).xy;
    //outputVelocity = texture(VelocityTexture, vec2(uv.x-0.1*iTimeDelta,uv.y)).xy;
    //outputVelocity = texture(VelocityTexture, vec2(uv.x-inverseResolution.x,uv.y)).xy;
    
    
    
    // Add force.
    if(uv.x > ForceAreaMin.x && uv.x < ForceAreaMax.x &&
       uv.y > ForceAreaMin.y && uv.y < ForceAreaMax.y)
    {
    	outputVelocity += Force * iTimeDelta;
        //outputVelocity = Force ;
    }
    
    // Clamp velocity at borders to zero.
    if(uv.x > 1.0 - inverseResolution.x ||
      	uv.y > 1.0 - inverseResolution.y ||
      	uv.x < inverseResolution.x ||
      	uv.y < inverseResolution.y)
    {
        outputVelocity = vec2(0.0, 0.0);
    }
    
    // Circle barrier.

    BarrierPosition = vec2(0.2, abs(sin(iTime))/2);
    vec2 toBarrier = BarrierPosition - uv;
    toBarrier.x *= inverseResolution.y / inverseResolution.x;
    //vec4 fragColorN = vec4(0.0);
    if(dot(toBarrier, toBarrier) < BarrierRadiusSq)
    {
        fragColor = vec4(0.0, 0.0, 999.0, 0.0);
    }
    else
    {
        fragColor = vec4(outputVelocity, 0.0, 0.0);

    } 

    


    // Encoding
    /* vec2 velocity = vec2(0.5, -0.3);
    vec4 fragColor = vec4(
                    max(0.0, velocity.x),   // Red: positive X
                    abs(min(0.0, velocity.x)),  // Green: negative X
                    max(0.0, velocity.y),   // Blue: positive Y
                    abs(min(0.0, velocity.y))   // Alpha: negative Y
                        );
     */

}

void main()
{
    mainImage(gl_FragColor, uv);
}