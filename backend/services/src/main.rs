"""
Edu-Flow Rust Microservices

This module provides AI-powered microservices for the Edu-Flow backend:
- Performance prediction using machine learning
- Course recommendations using collaborative filtering
- Knowledge search and analytics
- Performance optimization services

Author: Edu-Flow Team
"""

use std::env;
use std::sync::Arc;
use std::time::Duration;
use tokio::time::{sleep, interval};
use tracing::{info, warn, error};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

use edu_flow_services::{
    ai_services::performance_prediction::PerformancePredictionService,
    ai_services::recommendation::CourseRecommendationService,
    ai_services::knowledge_search::KnowledgeSearchService,
    database::DatabasePool,
    cache::CacheManager,
    config::Config,
    api::server::start_api_server,
    monitoring::MetricsCollector,
};

mod ai_services;
mod database;
mod cache;
mod config;
mod api;
mod monitoring;
mod utils;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize tracing
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "edu_flow_services=info".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    info!("Starting Edu-Flow Rust Microservices");

    // Load configuration
    let config = Config::from_env()
        .unwrap_or_else(|e| {
            error!("Failed to load configuration: {}", e);
            std::process::exit(1);
        });

    // Initialize database pool
    let db_pool = DatabasePool::new(&config.database_url)
        .await
        .unwrap_or_else(|e| {
            error!("Failed to initialize database pool: {}", e);
            std::process::exit(1);
        });

    // Initialize cache
    let cache_manager = CacheManager::new(&config.redis_url)
        .await
        .unwrap_or_else(|e| {
            error!("Failed to initialize cache: {}", e);
            std::process::exit(1);
        });

    // Initialize AI services
    let performance_service = PerformancePredictionService::new(&config.ai_model_path)
        .await?;
    
    let recommendation_service = CourseRecommendationService::new(&config.recommendation_model_path)
        .await?;
    
    let knowledge_service = KnowledgeSearchService::new(&config.knowledge_base_path)
        .await?;

    // Initialize metrics collector
    let metrics = MetricsCollector::new();

    // Start background tasks
    start_background_tasks(
        &db_pool,
        &cache_manager,
        &performance_service,
        &recommendation_service,
        &knowledge_service,
        &metrics,
        &config,
    ).await?;

    // Start API server
    info!("Starting API server on port {}", config.api_port);
    start_api_server(
        config.api_port,
        db_pool,
        cache_manager,
        performance_service,
        recommendation_service,
        knowledge_service,
        metrics,
    ).await?;

    Ok(())
}

async fn start_background_tasks(
    db_pool: &DatabasePool,
    cache_manager: &CacheManager,
    performance_service: &PerformancePredictionService,
    recommendation_service: &CourseRecommendationService,
    knowledge_service: &KnowledgeSearchService,
    metrics: &MetricsCollector,
    config: &Config,
) -> Result<(), Box<dyn std::error::Error>> {
    // Model warm-up task
    tokio::spawn({
        let db_pool = db_pool.clone();
        let performance_service = performance_service.clone();
        let recommendation_service = recommendation_service.clone();
        let knowledge_service = knowledge_service.clone();
        
        async move {
            info!("Starting model warm-up");
            
            // Warm up ML models
            if let Err(e) = performance_service.warm_up().await {
                error!("Performance service warm-up failed: {}", e);
            }
            
            if let Err(e) = recommendation_service.warm_up().await {
                error!("Recommendation service warm-up failed: {}", e);
            }
            
            if let Err(e) = knowledge_service.warm_up().await {
                error!("Knowledge service warm-up failed: {}", e);
            }
            
            info!("Model warm-up completed");
        }
    });

    // Cache warming task
    tokio::spawn({
        let cache_manager = cache_manager.clone();
        let db_pool = db_pool.clone();
        
        async move {
            info!("Starting cache warming");
            
            loop {
                if let Err(e) = warm_up_cache(&cache_manager, &db_pool).await {
                    error!("Cache warming failed: {}", e);
                }
                
                sleep(Duration::from_secs(config.cache_warm_up_interval)).await;
            }
        }
    });

    // Metrics collection task
    tokio::spawn({
        let metrics = metrics.clone();
        let db_pool = db_pool.clone();
        
        async move {
            info!("Starting metrics collection");
            
            let mut interval = interval(Duration::from_secs(config.metrics_collection_interval));
            
            loop {
                interval.tick().await;
                
                if let Err(e) = collect_metrics(&metrics, &db_pool).await {
                    error!("Metrics collection failed: {}", e);
                }
            }
        }
    });

    // Health check task
    tokio::spawn({
        let db_pool = db_pool.clone();
        let cache_manager = cache_manager.clone();
        
        async move {
            info!("Starting health checks");
            
            loop {
                if let Err(e) = perform_health_checks(&db_pool, &cache_manager).await {
                    error!("Health check failed: {}", e);
                }
                
                sleep(Duration::from_secs(config.health_check_interval)).await;
            }
        }
    });

    Ok(())
}

async fn warm_up_cache(
    cache_manager: &CacheManager,
    db_pool: &DatabasePool,
) -> Result<(), Box<dyn std::error::Error>> {
    info!("Warming up cache");
    
    // Warm up frequently accessed data
    let users = db_pool.get_active_users().await?;
    for user in users {
        cache_manager.set_user_profile(&user.id, &user).await?;
    }
    
    let courses = db_pool.get_popular_courses().await?;
    for course in courses {
        cache_manager.set_course_data(&course.id, &course).await?;
    }
    
    info!("Cache warming completed");
    Ok(())
}

async fn collect_metrics(
    metrics: &MetricsCollector,
    db_pool: &DatabasePool,
) -> Result<(), Box<dyn std::error::Error>> {
    // Collect database metrics
    let db_metrics = db_pool.get_metrics().await?;
    metrics.set_database_metrics(db_metrics);
    
    // Collect system metrics
    let system_metrics = metrics.get_system_metrics().await?;
    metrics.set_system_metrics(system_metrics);
    
    // Collect AI service metrics
    let ai_metrics = metrics.get_ai_service_metrics().await?;
    metrics.set_ai_service_metrics(ai_metrics);
    
    Ok(())
}

async fn perform_health_checks(
    db_pool: &DatabasePool,
    cache_manager: &CacheManager,
) -> Result<(), Box<dyn std::error::Error>> {
    // Check database connectivity
    db_pool.health_check().await?;
    
    // Check cache connectivity
    cache_manager.health_check().await?;
    
    Ok(())
}