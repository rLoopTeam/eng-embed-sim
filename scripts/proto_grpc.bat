REM Create the protobuf / GRPC server files
REM Run this from the 'scripts' directory
REM Also remember to activate the virtualenv (../../env/Scripts/activate probably)

python -m grpc_tools.protoc -I../protos --python_out=../rloopsim --grpc_python_out=../rloopsim ../protos/simulator_control.proto