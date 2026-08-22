{
  lib,
  python3Packages,
  libappindicator,
  gobject-introspection,
  wrapGAppsHook4,
  bash,
  pipewire,
  gtk4,
}:
let
  pname = "pulsemeeter";
  src = ./../..;
  version =
    let
      matches = builtins.match ".*VERSION = ['\"]([^'\"]+)['\"].*" (
        builtins.readFile (src + "/src/${pname}/settings.py")
      );
    in
    if matches == null then throw "VERSION not found in settings.py" else builtins.head matches;
in
python3Packages.buildPythonApplication {
  pyproject = true;

  inherit pname version src;

  build-system = with python3Packages; [
    setuptools
    babel
  ];

  dependencies = with python3Packages; [
    pygobject3
    pydantic
    pulsectl
    pulsectl-asyncio
  ];

  nativeBuildInputs = [
    wrapGAppsHook4
    gobject-introspection
  ];

  buildInputs = [
    libappindicator
    pipewire
    bash
    gtk4
  ];

  makeWrapperArgs = [
    "\${gappsWrapperArgs[@]}"
  ];

  dontWrapGApps = true;

  pythonImportsCheck = [ pname ];

  meta = {
    description = "A pulseaudio and pipewire audio routing application";
    license = lib.licenses.mit;
    homepage = "https://github.com/theRealCarneiro/pulsemeeter";
    mainProgram = pname;
    platforms = lib.platforms.linux;
  };
}
