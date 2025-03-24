#version 330

//uniform vec2 iResolution;
//vec2 iResolution = vec2(1,1);

uniform sampler2D iChannel0;
uniform sampler2D iChannel1;
uniform sampler2D iChannel2;
//uniform float iTimeDelta;
in vec2 uv;
out vec4 fragColor;


#define VELOCITY 0 
#define PRESSURE 1
#define DIVERGENCE 2

#define SHOW VELOCITY


vec4 showPressure(vec2 uv)
{
    return abs(texture(iChannel2, uv)) * 0.05;
}

vec4 showVelocity(vec2 uv)
{
    vec4 color = texture(iChannel0, uv);
    if(color.z > 0.0) // obstacle
    {
        return vec4(0.5);
    }
    else
    {
        return abs(color.gbra) * 0.1;
        //return vec4(abs(color.b), 1.0 - abs(color.gr), 1.0) * 0.008;
    }
}

vec4 showDivergence(vec2 uv)
{
    // Divergence should be as close to 0 as possible.. sadly it isn't.
    return abs(texture(iChannel1, uv));
}

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    //vec2 uv = fragCoord.xy / iResolution.xy;

    #if SHOW == VELOCITY
    fragColor = showVelocity(uv);
    #elif SHOW == PRESSURE
    fragColor = showPressure(uv);
    #elif SHOW == DIVERGENCE
    fragColor = showDivergence(uv);
    #endif
}

void main()
{
    mainImage(fragColor, uv);
}