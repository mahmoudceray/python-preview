const path = require('path');
const webpack = require('webpack');
const CopyPlugin = require('copy-webpack-plugin');

module.exports = {
    entry: './index.ts',

    output: {
        path: path.resolve(__dirname, '..', 'assets'),
        filename: 'index.js',
        clean: true
    },

    module: {
        rules: [
            {
                test: /\.ts$/,
                use: {
                    loader: 'ts-loader',
                    options: {
                        transpileOnly: true
                    }
                },
                exclude: /node_modules/
            }
        ]
    },

    resolve: {
        extensions: ['.ts', '.js'],
        alias: {
            "jquery": path.resolve(__dirname, 'lib', 'jquery-3.7.1.min.js'),
            "$": path.resolve(__dirname, 'lib', 'jquery-3.7.1.min.js'),
            "$.bbq": path.resolve(__dirname, 'lib', 'jquery.ba-bbq.js')
        }
    },

    plugins: [
        new webpack.ProvidePlugin({
            jquery: "jquery",
            jQuery: "jquery",
            $: 'jquery'
        }),
        new CopyPlugin({
            patterns: [
                {
                    from: path.resolve(__dirname, 'lib', 'jquery-ui-1.13.2', 'jquery-ui.min.css'),
                    to: path.resolve(__dirname, '..', 'assets', 'jquery-ui.min.css')
                },
                {
                    from: path.resolve(__dirname, 'lib', 'jquery-ui-1.13.2', 'images'),
                    to: path.resolve(__dirname, '..', 'assets', 'images')
                },
                {
                    from: path.resolve(__dirname, 'lib', 'pytutor.common.css'),
                    to: path.resolve(__dirname, '..', 'assets', 'pytutor.common.css')
                },
                {
                    from: path.resolve(__dirname, 'lib', 'pytutor.theme.css'),
                    to: path.resolve(__dirname, '..', 'assets', 'pytutor.theme.css')
                }
            ]
        })
    ]
};
