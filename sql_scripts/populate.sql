INSERT INTO feedbacks (id, feedback, sentiment, feature_code, feature_reason, created_at) VALUES
    ('FB001', 'Estou adorando o aplicativo! As meditações guiadas são muito relaxantes e me ajudam a dormir melhor. Seria ótimo ter mais opções de meditação para dormir.', 
    'POSITIVO', 'MAIS_MEDITACOES', 'Usuário solicita mais opções de meditações para dormir',
    NOW() - INTERVAL '6 days'),

    ('FB002', 'O app está muito bom, mas tem um botão fantasma aparecendo na tela inicial que some quando tento clicar. Isso está atrapalhando a navegação.',
    'POSITIVO', 'CORRIGIR_UI', 'Botão fantasma aparecendo e desaparecendo na interface',
    NOW() - INTERVAL '5 days'),

    ('FB003', 'Péssima experiência! O app trava constantemente durante as sessões de meditação, perdendo todo o progresso. Muito frustrante.',
    'NEGATIVO', 'CORRIGIR_UI', 'App trava durante as sessões de meditação',
    NOW() - INTERVAL '4 days'),

    ('FB004', 'Excelente aplicativo! Tem me ajudado muito com ansiedade. Seria interessante ter uma opção para compartilhar o progresso com amigos.',
    'POSITIVO', 'COMPARTILHAR', 'Adicionar função para compartilhar progresso com amigos',
    NOW() - INTERVAL '3 days'),

    ('FB005', 'Estou vendo o mesmo botão fantasma que outros usuários reportaram. Fora isso, o app é perfeito para minhas necessidades diárias de meditação.',
    'POSITIVO', 'CORRIGIR_UI', 'Confirmação do problema do botão fantasma na interface',
    NOW() - INTERVAL '2 days'),

    ('FB006', 'Não consigo usar o app direito, toda hora aparece um botão que some quando vou clicar. Muito irritante!',
    'NEGATIVO', 'CORRIGIR_UI', 'Usuário frustrado com o botão fantasma na interface',
    NOW() - INTERVAL '1 day'),

    ('FB007', 'Fantástico! As sessões de terapia online são muito práticas. Sugiro adicionar lembretes personalizados para as sessões.',
    'POSITIVO', 'LEMBRETES', 'Implementar sistema de lembretes para sessões',
    NOW() - INTERVAL '12 hours'),

    ('FB008', 'Muito bom o app! Uso todos os dias para meditar. Seria legal ter mais vozes diferentes para as meditações guiadas.',
    'POSITIVO', 'MAIS_VOZES', 'Adicionar mais opções de narradores para meditações',
    NOW());
